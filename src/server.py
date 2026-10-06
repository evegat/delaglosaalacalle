"""
Backend API para "De la Glosa a la Calle"
FastAPI + SQLite + DuckDB

Funcionalidades:
1. Servir archivos estáticos del frontend (dist/)
2. GET /api/countdown -> Segundos restantes hasta Lunes 05 de Octubre 2026 08:00 AM CLST
3. POST /api/preguntas -> Recibe preguntas ciudadanas, las persiste en SQLite y busca coincidencias con programas DIPRES
4. GET /api/preguntas -> Lista preguntas ciudadanas recientes
5. GET /api/programas -> Consulta y filtrado de los 166 programas evaluados
"""

import datetime
import csv
import hashlib
import html
import json
import logging
import os
import re
import sqlite3
import time
import unicodedata
from contextlib import closing, asynccontextmanager
from pathlib import Path
from typing import Optional

import duckdb
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from bajada_calle import calcular_bajada_calle

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
DATA_DIR = Path(os.environ.get("P149_DATA_DIR", str(BASE_DIR / "data")))
DB_PATH = DATA_DIR / "presupuesto_compras_db.duckdb"
SQLITE_PATH = Path(os.environ.get("P149_SQLITE_PATH", str(DATA_DIR / "preguntas_ciudadanas.sqlite3")))

# Fecha objetivo: Lunes 05 de Octubre 2026, 08:00 AM Hora de Chile (UTC-3)
OBJETIVO_LUNES = datetime.datetime(2026, 10, 5, 8, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=-3)))
RATE_LIMIT = max(1, int(os.environ.get("P149_RATE_LIMIT", "5")))
RATE_WINDOW_SECONDS = max(1, int(os.environ.get("P149_RATE_WINDOW_SECONDS", "600")))
logger = logging.getLogger("p149")


@asynccontextmanager
async def lifespan(_app):
    init_sqlite()
    yield

app = FastAPI(
    title="De la Glosa a la Calle API",
    description="Observatorio Cívico de Gasto Fiscal y Compras Públicas",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.path not in {"/docs", "/redoc"}:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "font-src 'self'; img-src 'self' data:; connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        )
    if request.url.path.startswith("/api/preguntas"):
        response.headers["Cache-Control"] = "no-store"
    return response

# Inicializar base de datos SQLite para preguntas con modo WAL y timeout
def init_sqlite():
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(get_db_connection()) as conn, conn:
        conn.execute("""
    CREATE TABLE IF NOT EXISTS preguntas_ciudadanas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        pregunta TEXT NOT NULL,
        comuna TEXT,
        contacto TEXT,
        programa_coincidente TEXT,
        motivo_hacienda TEXT,
        respondida_en_vivo BOOLEAN DEFAULT FALSE
    );
        """)
        conn.execute("""CREATE TABLE IF NOT EXISTS limites_preguntas (
            clave TEXT PRIMARY KEY, ventana INTEGER NOT NULL,
            contador INTEGER NOT NULL CHECK(contador >= 0)
        )""")

def get_db_connection():
    conn = sqlite3.connect(SQLITE_PATH, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn

class PreguntaInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    pregunta: str = Field(..., min_length=4, max_length=500)
    comuna: Optional[str] = Field(None, max_length=100)
    contacto: Optional[str] = Field(None, max_length=150)
    consentimiento_contacto: bool = False

    @field_validator("pregunta", "comuna", "contacto", mode="before")
    @classmethod
    def texto_plano(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Usa texto, no objetos ni números.")
        value = unicodedata.normalize("NFC", html.unescape(value))
        if any(unicodedata.category(c).startswith("C") and c not in "\n\r\t" for c in value):
            raise ValueError("El texto contiene caracteres de control.")
        if re.search(r"<[^>]+>", value):
            raise ValueError("Escribe texto sin etiquetas HTML.")
        return " ".join(value.split())

    @field_validator("pregunta")
    @classmethod
    def pregunta_significativa(cls, value):
        if sum(c.isalpha() for c in value) < 4:
            raise ValueError("Describe tu pregunta con al menos cuatro letras.")
        return value

    @model_validator(mode="after")
    def contacto_con_consentimiento(self):
        if self.contacto and not self.consentimiento_contacto:
            raise ValueError("Para guardar contacto se requiere consentimiento explícito.")
        return self


STOPWORDS = set("a al algo ante como con cual cuando de del el en es esa ese esta este hay la las lo los mas me mi para por que qué se si sin sobre su sus un una unos unas y yo afecta afectara pasa pasara cambia cambiara presupuesto presupuestario recorte recortes consulta quisiera saber ocurre recursos".split())


def terminos_busqueda(texto):
    normal = "".join(c for c in unicodedata.normalize("NFKD", texto.casefold()) if not unicodedata.combining(c))
    return list(dict.fromkeys(t for t in re.findall(r"[a-z0-9]+", normal) if len(t) >= 3 and t not in STOPWORDS))[:12]


def buscar_programas(texto=None, limit=200, servicio=None):
    """Búsqueda textual compuesta; no inferencia semántica ni respuesta personalizada."""
    tokens = terminos_busqueda(texto) if texto else []
    if texto and not tokens:
        return []
    if not DB_PATH.exists():
        raise duckdb.IOException("Analítica no disponible")
    fields = ["nombre_programa", "ministerio", "servicio", "motivo_variacion_presupuestaria"]
    expressions = [f"strip_accents(lower(coalesce({f}, '')))" for f in fields]
    document = " || ' ' || ".join(expressions)
    where = " AND ".join(f"({document}) LIKE ?" for _ in tokens) or "TRUE"
    score = " + ".join(f"CASE WHEN {expressions[0]} LIKE ? THEN 3 ELSE 1 END" for _ in tokens) or "0"
    params = [f"%{t}%" for t in tokens] * 2
    if servicio:
        where += " AND servicio = ?"
        params.append(servicio)
    params.append(limit)
    with closing(duckdb.connect(str(DB_PATH), read_only=True)) as con:
        frame = con.execute(f"""SELECT * EXCLUDE (score) FROM (
            SELECT *, ({score}) AS score FROM programas_evaluados_dipres WHERE {where}
        ) ORDER BY score DESC, variacion_presupuesto_2025_2026_pct ASC NULLS LAST, nombre_programa LIMIT ?""", params).fetchdf()
    return json.loads(frame.to_json(orient="records", force_ascii=False))

@app.get("/api/countdown")
def get_countdown():
    ahora = datetime.datetime.now(datetime.timezone.utc)
    delta = OBJETIVO_LUNES - ahora
    segundos_totales = int(max(0, delta.total_seconds()))
    horas = segundos_totales // 3600
    minutos = (segundos_totales % 3600) // 60
    segundos = segundos_totales % 60
    
    return {
        "objetivo_iso": OBJETIVO_LUNES.isoformat(),
        "finalizado": segundos_totales <= 0,
        "segundos_totales": segundos_totales,
        "desglose": {
            "horas": horas,
            "minutos": minutos,
            "segundos": segundos
        },
        "mensaje": "Objetivo operativo de preparación del proyecto: lunes 5 de octubre a las 08:00, hora de Chile. Disponibilidad de fuentes por verificar."
    }

@app.post("/api/preguntas")
def crear_pregunta(payload: PreguntaInput, request: Request):
    texto = payload.pregunta
    
    # Coincidencia textual: considera todos los términos útiles y sus acentos.
    match_programa = None
    motivo_hacienda = None
    
    busqueda_disponible = True
    try:
        matches = buscar_programas(texto, limit=3)
        if matches:
            match_programa = matches[0]["nombre_programa"]
            motivo_hacienda = matches[0].get("motivo_variacion_presupuestaria")
    except duckdb.Error:
        busqueda_disponible = False
        logger.warning("p149_search_unavailable")
    
    # Persistir en SQLite con WAL y busy_timeout
    now = int(time.time())
    ventana = now // RATE_WINDOW_SECONDS
    retry = RATE_WINDOW_SECONDS - now % RATE_WINDOW_SECONDS
    # Request.client solo: nunca confiar directamente en X-Forwarded-For del usuario.
    client = request.client.host if request.client else "unknown"
    clave = hashlib.sha256(client.encode("utf-8")).hexdigest()
    try:
        with closing(get_db_connection()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM limites_preguntas WHERE ventana < ?", (ventana - 1,))
            previous = conn.execute("SELECT ventana, contador FROM limites_preguntas WHERE clave=?", (clave,)).fetchone()
            count = previous[1] if previous and previous[0] == ventana else 0
            if count >= RATE_LIMIT:
                conn.rollback()
                raise HTTPException(429, "Alcanzaste el límite de preguntas. Intenta más tarde.", headers={"Retry-After": str(retry)})
            conn.execute("""INSERT INTO limites_preguntas VALUES (?,?,?)
                ON CONFLICT(clave) DO UPDATE SET ventana=excluded.ventana, contador=excluded.contador""", (clave, ventana, count + 1))
            cur = conn.execute("""INSERT INTO preguntas_ciudadanas
                (pregunta, comuna, contacto, programa_coincidente, motivo_hacienda, respondida_en_vivo)
                VALUES (?, ?, ?, ?, ?, ?)""", (texto, payload.comuna, payload.contacto, match_programa, motivo_hacienda, False))
            qid = cur.lastrowid
            conn.commit()
    except sqlite3.OperationalError:
        logger.warning("p149_question_store_unavailable")
        raise HTTPException(503, "No pudimos guardar la pregunta. Conserva el texto e intenta nuevamente.", headers={"Retry-After": "5"}) from None
    
    return {
        "ok": True,
        "id": qid,
        "match_encontrado": match_programa is not None,
        "programa": match_programa,
        "motivo_hacienda": motivo_hacienda,
        "tipo_coincidencia": "textual_orientativa",
        "periodo_datos": "2025–2026",
        "respuesta_personalizada": False,
        "busqueda_disponible": busqueda_disponible,
        "mensaje_respuesta": (
            f"Pregunta guardada. Encontramos una coincidencia textual con {match_programa} en datos 2025–2026. No es una respuesta personalizada ni acredita un impacto en tu comuna."
            if match_programa else
            "Pregunta guardada. No encontramos una coincidencia textual verificable; queda pendiente de revisión."
        )
    }

@app.get("/api/preguntas")
def listar_preguntas(limit: int = Query(10, ge=1, le=50)):
    # Solo metadatos públicos. El texto libre y la comuna pueden revelar datos personales.
    try:
        with closing(get_db_connection()) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""SELECT id, fecha, programa_coincidente, respondida_en_vivo
                FROM preguntas_ciudadanas ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()
            return [dict(row) for row in rows]
    except sqlite3.OperationalError:
        raise HTTPException(503, "El registro de preguntas no está disponible.") from None

@app.get("/api/programas")
def listar_programas(q: Optional[str] = Query(None, max_length=200),
                     servicio: Optional[str] = Query(None, max_length=200)):
    try:
        return buscar_programas(q, servicio=servicio)
    except duckdb.Error:
        raise HTTPException(503, "La base analítica no está disponible. Puedes consultar la descarga publicada.") from None

@app.get('/api/servicios')
def listar_servicios():
    try:
        with closing(duckdb.connect(str(DB_PATH), read_only=True)) as con:
            return [r[0] for r in con.execute("SELECT DISTINCT servicio FROM programas_evaluados_dipres WHERE servicio IS NOT NULL ORDER BY servicio").fetchall()]
    except duckdb.Error:
        raise HTTPException(503, 'El catálogo de servicios no está disponible.') from None


@app.get('/api/comparacion')
def comparacion_presupuesto():
    path = Path(os.environ.get('P149_INGESTA_DB', str(DATA_DIR / 'ingesta.sqlite3')))
    if not path.is_file():
        return {'estado': 'no_disponible', 'datos': [],
                'motivo': 'Falta ingesta verificada con seis códigos completos para 2025 y 2026. Ausencia no equivale a cero.'}
    try:
        try:
            from .ingesta_batch import comparar_sqlite
        except ImportError:
            from ingesta_batch import comparar_sqlite
        return {'estado': 'disponible', 'datos': comparar_sqlite(path),
                'motivo': 'Variación real no disponible sin IPC oficial verificado del período.'}
    except (sqlite3.Error, ValueError):
        raise HTTPException(503, 'La comparación presupuestaria no está disponible.') from None


@app.get('/api/equivalencias')
def catalogo_equivalencias():
    try:
        from .equivalencias_civicas import resumir_catalogo
    except ImportError:
        from equivalencias_civicas import resumir_catalogo
    path = DATA_DIR / 'costos_referencia.csv'
    if not path.is_file():
        return {'estado': 'sin_referencias_verificadas', 'grupos': [], 'excluidas': []}
    with path.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row['verificada'] = str(row.get('verificada', '')).lower() == 'true'
    resumen = resumir_catalogo(rows)
    return resumen


@app.get('/api/presupuesto2027')
def listar_presupuesto_2027(
    partida: Optional[str] = Query(None, description="Filtrar por código de partida (ej. 05, 09, 29, 31)"),
    q: Optional[str] = Query(None, description="Búsqueda textual por nombre o código"),
    orden: Optional[str] = Query(None, description="criterio de orden: 'mayor_recorte', 'mayor_aumento', 'monto_2027'")
):
    json_path = DATA_DIR / 'comparativa_programas_2026_2027.json'
    if not json_path.is_file():
        raise HTTPException(404, "Base comparativa 2026-2027 no encontrada.")
    with open(json_path, encoding='utf-8') as f:
        datos = json.load(f)

    if partida:
        p_clean = partida.zfill(2)
        datos = [d for d in datos if d.get('partida') == p_clean]

    if q:
        q_norm = "".join(c for c in unicodedata.normalize("NFKD", q.casefold()) if not unicodedata.combining(c))
        tokens = [t for t in q_norm.split() if len(t) >= 2]
        def match_item(d):
            txt = f"{d.get('codigo','')} {d.get('nombre_partida','')} {d.get('nombre_capitulo','')} {d.get('nombre_programa','')}"
            txt_norm = "".join(c for c in unicodedata.normalize("NFKD", txt.casefold()) if not unicodedata.combining(c))
            # Alias cívicos directos para ciudadanos comunes
            if "servicio local" in txt_norm:
                txt_norm += " slep sleps escuela escuelas colegios educacion publica"
            if "recuperacion de barrios" in txt_norm or "quiero mi barrio" in txt_norm:
                txt_norm += " quiero mi barrio barrio barrios plazas luminarias"
            if "asentamientos precarios" in txt_norm or "campamentos" in txt_norm:
                txt_norm += " campamento campamentos tomas agua potable"
            if "becas y asistencialidad" in txt_norm or "junaeb" in txt_norm:
                txt_norm += " yo elijo mi pc becas tic computador computadores pc pcs notebook notebooks escolares"
            if d.get('partida') == '16':
                txt_norm += " salud hospital hospitales cesfam consultorio consultorios camas urgencia cirugia cirugias medico medicos"
            return all(t in txt_norm for t in tokens)
        datos = [d for d in datos if match_item(d)]

    if orden == 'mayor_recorte':
        datos = sorted(datos, key=lambda x: (x.get('dif_vs_ini_mclp') or 0))
    elif orden == 'mayor_aumento':
        datos = sorted(datos, key=lambda x: (x.get('dif_vs_ini_mclp') or 0), reverse=True)
    elif orden == 'monto_2027':
        datos = sorted(datos, key=lambda x: (x.get('proy_2027_mclp') or 0), reverse=True)

    # Métricas agregadas
    tot_ini = sum(d.get('ini_2026_mclp', 0) for d in datos)
    tot_vig = sum(d.get('vig_2026_mclp', 0) for d in datos)
    tot_proy = sum(d.get('proy_2027_mclp', 0) for d in datos)

    for d in datos:
        d['bajada_calle'] = calcular_bajada_calle(d)

    return {
        'total_programas': len(datos),
        'totales_mclp': {
            'inicial_2026': tot_ini,
            'vigente_2026': tot_vig,
            'proyecto_2027': tot_proy,
            'dif_vs_ini': tot_proy - tot_ini,
            'dif_vs_vig': tot_proy - tot_vig
        },
        'programas': datos
    }


@app.get('/api/articulado')
def obtener_articulado():
    """Retorna la matriz comparativa de articulado: Ley 2026 vs Proyecto 2027."""
    json_path = DATA_DIR / 'matriz_articulado_2026_2027.json'
    if not json_path.is_file():
        raise HTTPException(404, "Matriz de articulado no disponible.")
    with open(json_path, encoding='utf-8') as f:
        return json.load(f)


@app.get('/api/recorrido/{programa_id}')
def obtener_recorrido(programa_id: str):
    """Mapea la transformación del recurso público a la calle:
    Origen fiscal -> Mecanismo (Subtítulo) -> Ejecutor/Contrato -> Bien tangible y dilema de calle.
    """
    if not DB_PATH.exists():
        raise HTTPException(503, "Base analítica no disponible.")
    with closing(duckdb.connect(str(DB_PATH), read_only=True)) as con:
        # Buscar por id_bips o coincidencia de nombre
        row = con.execute("""
            SELECT id_bips, ministerio, servicio, nombre_programa, presupuesto_2026_m$,
                   variacion_presupuesto_2025_2026_pct, asignacion, antecedentes_generales,
                   poblacion, descripcion, motivo_variacion_presupuestaria
            FROM programas_evaluados_dipres
            WHERE CAST(id_bips AS VARCHAR) = ? OR nombre_programa = ?
            LIMIT 1
        """, (programa_id, programa_id)).fetchone()
        
        if not row:
            # Fallback a la base comparativa 2027
            json_path = DATA_DIR / 'comparativa_programas_2026_2027.json'
            if json_path.is_file():
                with open(json_path, encoding='utf-8') as f:
                    progs_2027 = json.load(f)
                matched = next((p for p in progs_2027 if p.get('codigo') == programa_id or p.get('nombre_programa') == programa_id), None)
                if matched:
                    bajada = calcular_bajada_calle(matched)
                    estaciones = [
                        {
                            "estacion": 1,
                            "fase": "Origen Fiscal",
                            "titulo": matched.get('nombre_partida') or f"Partida {matched.get('partida')}",
                            "detalle": f"Capítulo: {matched.get('nombre_capitulo')} · Programa: {matched.get('nombre_programa')}",
                            "tipo": "institucional"
                        },
                        {
                            "estacion": 2,
                            "fase": "Mecanismo Presupuestario",
                            "titulo": f"Presupuesto 2027: ${matched.get('proy_2027_mclp', 0):,} M$",
                            "detalle": f"Variación vs Inicial 2026: {matched.get('pct_vs_ini')}% (Dif: ${matched.get('dif_vs_ini_mclp', 0):,} M$)",
                            "regla_ejecucion": "Ley de Presupuestos del Sector Público",
                            "tipo": "normativo"
                        },
                        {
                            "estacion": 3,
                            "fase": "Gestión y Compras Públicas",
                            "titulo": bajada['organismo'] if bajada else (matched.get('nombre_capitulo') or "Organismo Ejecutor"),
                            "detalle": f"Referencia: {bajada['contrato_ref']}" if bajada else "Convenio de Transferencia / Licitación Pública",
                            "tipo": "operacional"
                        },
                        {
                            "estacion": 4,
                            "fase": "En la Calle",
                            "titulo": bajada['impacto_texto'] if bajada else "Prestaciones territoriales",
                            "costo_unitario_referencia": bajada['costo_unitario_clp'] if bajada else None,
                            "dilema_calle": bajada['dilema'] if bajada else "Impacto en lista de espera y cobertura directa a beneficiarios",
                            "tipo": "calle"
                        }
                    ]
                    return {
                        "programa": {
                            "nombre_programa": matched.get('nombre_programa'),
                            "servicio": matched.get('nombre_capitulo'),
                            "ministerio": matched.get('nombre_partida'),
                            "presupuesto_2026_m$": matched.get('ini_2026_mclp'),
                            "variacion_pct": matched.get('pct_vs_ini'),
                            "descripcion": f"Programa oficial de la Partida {matched.get('partida')}, analizado en la comparativa multiserie 2026-2027 con datos de la Ley de Presupuestos."
                        },
                        "bajada_calle": bajada,
                        "estaciones": estaciones
                    }
            raise HTTPException(404, f"Programa '{programa_id}' no encontrado en el catálogo oficial.")
        
        cols = ['id_bips', 'ministerio', 'servicio', 'nombre_programa', 'presupuesto_2026_m$',
                'variacion_pct', 'asignacion', 'antecedentes', 'poblacion', 'descripcion', 'motivo_variacion']
        prog = dict(zip(cols, row))
        
        # Deducción del mecanismo a partir de la asignación presupuestaria (subtítulo)
        asig = prog['asignacion'] or ''
        subtitulo_num = '24'
        mecanismo = 'Transferencias Corrientes (Convenios con municipios / terceros)'
        tipo_ejecucion = 'Convenio de Transferencia (Rendición CGR / SISREC)'
        
        if '-21-' in asig or '21' in asig[:10]:
            subtitulo_num = '21'
            mecanismo = 'Gastos en Personal (Funcionarios públicos / dotación)'
            tipo_ejecucion = 'Remuneración y carrera funcionaria'
        elif '-22-' in asig or '22' in asig[:10]:
            subtitulo_num = '22'
            mecanismo = 'Bienes y Servicios de Consumo (Compras e insumos)'
            tipo_ejecucion = 'Licitación / Orden de Compra en Mercado Público'
        elif '-31-' in asig or '-33-' in asig or 'Iniciativas de Inversión' in asig:
            subtitulo_num = '31'
            mecanismo = 'Iniciativas de Inversión / Transferencias de Capital (Obras)'
            tipo_ejecucion = 'Licitación pública de obras de infraestructura'
        
        # Buscar compra emblemática asociada en la misma área o servicio
        nombre_lower = (prog['nombre_programa'] or '').lower()
        servicio_lower = (prog['servicio'] or '').lower()
        compra_row = None
        
        if any(k in nombre_lower for k in ['recién nacido', 'ajuar', 'parn', 'chile crece']):
            compra_row = con.execute("SELECT * FROM catalogo_compras_emblematicas WHERE rubro='SALUD_INFANCIA_PARN' LIMIT 1").fetchone()
        elif any(k in nombre_lower or k in servicio_lower for k in ['niñez', 'mejor niñez', 'peritaje', 'protección especializada']):
            compra_row = con.execute("SELECT * FROM catalogo_compras_emblematicas WHERE rubro='INFANCIA_PERITAJES' LIMIT 1").fetchone()
        elif any(k in nombre_lower or k in servicio_lower for k in ['colegio', 'escuela', 'educación', 'junaeb', 'infraestructura escolar']):
            compra_row = con.execute("SELECT * FROM catalogo_compras_emblematicas WHERE rubro='EDUCACION_MANTENCION' LIMIT 1").fetchone()
        elif any(k in nombre_lower or k in servicio_lower for k in ['cultura', 'arte', 'artístico']):
            compra_row = con.execute("SELECT * FROM catalogo_compras_emblematicas WHERE rubro='CULTURA_TALLERES' LIMIT 1").fetchone()
        elif any(k in nombre_lower or k in servicio_lower for k in ['regional', 'barrio', 'luminaria', 'fril', 'gore']):
            compra_row = con.execute("SELECT * FROM catalogo_compras_emblematicas WHERE rubro='GORE_ESPACIOS_PUBLICOS' LIMIT 1").fetchone()
        
        compra_detalle = None
        if compra_row:
            ccols = ['rubro', 'codigo_oc', 'organismo_comprador', 'nombre_contrato', 'proveedor',
                     'monto_clp', 'costo_unitario_estimado', 'unidad_fisica', 'dilema_calle']
            compra_detalle = dict(zip(ccols, compra_row))
        
        estaciones = [
            {
                "estacion": 1,
                "fase": "Origen Fiscal",
                "titulo": f"Partida {prog['ministerio']}",
                "detalle": f"Servicio: {prog['servicio']} · Asignación: {prog['asignacion'] or 'Glosa presupuestaria anual'}",
                "tipo": "institucional"
            },
            {
                "estacion": 2,
                "fase": "Mecanismo de Gasto",
                "titulo": f"Subtítulo {subtitulo_num}",
                "detalle": mecanismo,
                "regla_ejecucion": tipo_ejecucion,
                "tipo": "normativo"
            },
            {
                "estacion": 3,
                "fase": "Gestión y Ejecución",
                "titulo": compra_detalle['organismo_comprador'] if compra_detalle else (prog['servicio'] or "Organismo Ejecutor / Municipio"),
                "detalle": (
                    f"Contrato Mercado Público: {compra_detalle['codigo_oc']} ({compra_detalle['nombre_contrato']}) adjudicado a {compra_detalle['proveedor']}"
                    if compra_detalle else
                    f"Convenio de ejecución / Fondo concursable para {prog['poblacion'] or 'beneficiarios territoriales'}"
                ),
                "tipo": "operacional"
            },
            {
                "estacion": 4,
                "fase": "En la Calle",
                "titulo": compra_detalle['unidad_fisica'] if compra_detalle else "Prestación o servicio entregado",
                "costo_unitario_referencia": compra_detalle['costo_unitario_estimado'] if compra_detalle else None,
                "dilema_calle": compra_detalle['dilema_calle'] if compra_detalle else "Impacto en lista de espera o calidad del servicio prestado a beneficiarios directos",
                "tipo": "calle"
            }
        ]
        
        return {
            "programa": prog,
            "mecanismo": {
                "subtitulo": subtitulo_num,
                "nombre": mecanismo,
                "tipo_ejecucion": tipo_ejecucion
            },
            "compra_referencia": compra_detalle,
            "estaciones": estaciones
        }


# Montar frontend estático si existe dist/
if DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088)
