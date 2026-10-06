"""
Exportador de artefactos estáticos para GitHub Pages y CDN.
Genera los archivos JSON completos para funcionamiento 100% offline y estático en docs/ y dist/.
"""
import json
import csv
from io import StringIO
import shutil
import unicodedata
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DIST_DIR = BASE_DIR / "dist"
DOCS_DIR = BASE_DIR / "docs"
PUBLIC_URL = "https://delaglosaalacalle.evegat.cl"

# Importar motor de bajada a la calle
import sys
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR / "scripts"))
from bajada_calle import calcular_bajada_calle
from presupuesto_ciudadano import preparar_programas, resumen_presupuestario, construir_recorrido

def leer_csv(path):
    # UTF-8 primero; Latin-1 sólo si el archivo realmente no es UTF-8.
    try:
        text = path.read_text(encoding='utf-8-sig')
    except UnicodeDecodeError:
        text = path.read_text(encoding='latin1')
    return csv.DictReader(StringIO(text))

def enriquecer_y_sanitizar_programas(progs):
    cat_path = DATA_DIR / "catalogo_programas_2027_dipres.json"
    cat_map = {}
    if cat_path.is_file():
        with open(cat_path, encoding="utf-8") as f:
            for item in json.load(f):
                cat_map[item["codigo"]] = item

    # Si algún programa no está en el catálogo, parsear XML oficial de respaldo
    xml_path = DATA_DIR / "proyecto_presupuesto_2027_dipres_oficial.xml"
    if len(cat_map) < len(progs) and xml_path.is_file():
        import xml.etree.ElementTree as ET
        ns = {"pi": "http://www.contraloria.cl/Informes/SP/PresupuestoInicial"}
        tree = ET.parse(xml_path)
        for ley in tree.getroot().findall("pi:LeyDePresupuesto", ns):
            p_cod = ley.findtext("pi:codigoPartida", default="", namespaces=ns).strip().zfill(2)
            c_cod = ley.findtext("pi:codigoCapitulo", default="", namespaces=ns).strip().zfill(2)
            pr_cod = ley.findtext("pi:codigoPrograma", default="", namespaces=ns).strip().zfill(2)
            code = f"{p_cod}-{c_cod}-{pr_cod}"
            if code not in cat_map:
                p_nom = ley.findtext("pi:nombrePartida", default="", namespaces=ns).strip()
                c_nom = ley.findtext("pi:nombreCapitulo", default="", namespaces=ns).strip()
                pr_nom = ley.findtext("pi:nombrePrograma", default="", namespaces=ns).strip()
                cuentas = ley.find("pi:CuentasPresupuestos", ns)
                gastos = {}
                if cuentas is not None:
                    for c in cuentas.findall("pi:Cuenta", ns):
                        if c.get("tipoCuenta") == "G":
                            sub = c.findtext("pi:subtitulo", default="", namespaces=ns).strip()
                            item = c.findtext("pi:item", default="", namespaces=ns).strip()
                            asig = c.findtext("pi:asignacion", default="", namespaces=ns).strip()
                            if item == "00" and asig == "000":
                                m = int(c.findtext("pi:montoCLP", default="0", namespaces=ns).strip())
                                gastos[sub] = gastos.get(sub, 0) + m
                cat_map[code] = {
                    "codigo": code, "nombre_partida": p_nom, "nombre_capitulo": c_nom,
                    "nombre_programa": pr_nom, "gastos_subtitulos": gastos
                }

    for p in progs:
        cat_item = cat_map.get(p.get("codigo"), {})
        gastos = cat_item.get("gastos_subtitulos", {})
        subtitulos = sorted([str(k) for k, v in gastos.items() if v > 0])
        p["subtitulos"] = subtitulos
        p["tiene_dotacion"] = "21" in subtitulos
        p["monto_personal_2027_mclp"] = int(gastos.get("21", 0))

        # Sanitización de nombres institucionales limpia en UTF-8
        for campo in ["nombre_partida", "nombre_capitulo", "nombre_programa"]:
            val = p.get(campo)
            if not val or "\ufffd" in val:
                val = cat_item.get(campo) or val
            if val:
                val = unicodedata.normalize("NFC", val)
            p[campo] = val
    return progs

def exportar_todo():
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DIST_DIR / "data").mkdir(exist_ok=True)
    (DOCS_DIR / "data").mkdir(exist_ok=True)

    # 1. Cargar y enriquecer comparativa 2026-2027
    comp_path = DATA_DIR / "comparativa_programas_2026_2027.json"
    with open(comp_path, encoding="utf-8") as f:
        progs_2027 = json.load(f)

    progs_2027 = enriquecer_y_sanitizar_programas(progs_2027)
    with open(comp_path, "w", encoding="utf-8") as f:
        json.dump(progs_2027, f, ensure_ascii=False, indent=2)

    # Sincronizar base DuckDB canónica
    try:
        from migrar_duckdb_determinista import migrar_duckdb
        migrar_duckdb()
    except Exception as exc:
        print(f"Advertencia al sincronizar DuckDB: {exc}")

    progs_2027 = preparar_programas(progs_2027)
    presupuesto2027_payload = {**resumen_presupuestario(progs_2027), 'programas': progs_2027}
    cobertura_presupuesto = (
        f"{len(progs_2027)} programas presupuestarios en "
        f"{len({p['partida'] for p in progs_2027 if p.get('partida')})} partidas"
    )

    # 2. Cargar catálogo de programas evaluados DIPRES
    prog_eval_path = DATA_DIR / "programas_evaluados_dipres.csv"
    programas_eval = []
    servicios_set = set()
    if prog_eval_path.is_file():
        if prog_eval_path.is_file():
            reader = leer_csv(prog_eval_path)
            for r in reader:
                p_item = {
                    "id_bips": r.get("id_bips") or r.get("id"),
                    "ministerio": r.get("ministerio"),
                    "servicio": r.get("servicio"),
                    "nombre_programa": r.get("nombre_programa"),
                    "presupuesto_2026_m$": float(r.get("presupuesto_2026_m$") or 0) if r.get("presupuesto_2026_m$") else None,
                    "variacion_pct": float(r.get("variacion_presupuesto_2025_2026_pct") or 0) if r.get("variacion_presupuesto_2025_2026_pct") else None,
                    "descripcion": r.get("descripcion") or r.get("antecedentes_generales")
                }
                programas_eval.append(p_item)
                if r.get("servicio"):
                    servicios_set.add(r.get("servicio").strip())

    servicios_list = sorted(list(servicios_set))

    # 3. Cargar costos de referencia
    costos_path = DATA_DIR / "costos_referencia.csv"
    equivalencias_grupos = []
    if costos_path.is_file():
        if costos_path.is_file():
            reader = leer_csv(costos_path)
            for r in reader:
                equivalencias_grupos.append({
                    "servicio": r.get("servicio"),
                    "territorio": r.get("territorio"),
                    "periodo": r.get("periodo"),
                    "n": int(r.get("n") or 0),
                    "unidad": r.get("unidad"),
                    "moneda": r.get("moneda"),
                    "p25": float(r.get("p25") or 0) if r.get("p25") else None,
                    "p50": float(r.get("p50") or 0) if r.get("p50") else None,
                    "p75": float(r.get("p75") or 0) if r.get("p75") else None,
                    "desviacion_estandar": float(r.get("desviacion_estandar") or 0) if r.get("desviacion_estandar") else None,
                    "limite": r.get("limite") or "Muestra observacional ChileCompra"
                })

    equivalencias_payload = {
        "limite_metodologico": "Muestras territoriales observacionales. No imputan precios cero ni predicen costos fijos futuros.",
        "grupos": equivalencias_grupos
    }

    # 4. Generar Diccionario Consolidado de Recorridos (Drawer)
    recorridos_dict = {}
    for p in progs_2027:
        rec_obj = construir_recorrido(p)
        recorridos_dict[p.get("codigo")] = rec_obj
        recorridos_dict[p.get("nombre_programa")] = rec_obj
        recorridos_dict[p.get("nombre_programa").casefold()] = rec_obj

    # También agregar los programas evaluados BIPS
    for pe in programas_eval:
        b_mock = calcular_bajada_calle({"nombre_programa": pe["nombre_programa"], "partida": "09", "dif_vs_ini_mclp": 0, "proy_2027_mclp": pe["presupuesto_2026_m$"]})
        estaciones_bips = [
            {
                "estacion": 1,
                "fase": "Origen Fiscal",
                "titulo": pe.get("ministerio") or "Ministerio",
                "detalle": f"Servicio: {pe.get('servicio')} · Programa: {pe.get('nombre_programa')}",
                "tipo": "institucional"
            },
            {
                "estacion": 2,
                "fase": "Mecanismo Presupuestario",
                "titulo": f"Presupuesto Base 2026: ${pe.get('presupuesto_2026_m$', 0) or 0:,.0f} M$",
                "detalle": f"Variación declarada: {pe.get('variacion_pct') or 0}%",
                "tipo": "normativo"
            },
            {
                "estacion": 3,
                "fase": "Gestión y Compras Públicas",
                "titulo": b_mock["organismo"] if b_mock else (pe.get("servicio") or "Servicio Ejecutor"),
                "detalle": f"Referencia: {b_mock['contrato_ref']}" if b_mock else "Convenio de Gestión Directa / Mercado Público",
                "tipo": "operacional"
            },
            {
                "estacion": 4,
                "fase": "En la Calle",
                "titulo": b_mock["impacto_texto"] if b_mock else "Servicios directos a la ciudadanía",
                "costo_unitario_referencia": b_mock["costo_unitario_clp"] if b_mock else None,
                "dilema_calle": b_mock["dilema"] if b_mock else "Continuidad operacional y calidad de atención en el territorio.",
                "tipo": "calle"
            }
        ]
        rec_bips = {
            "programa": {
                "nombre_programa": pe.get("nombre_programa"),
                "servicio": pe.get("servicio"),
                "ministerio": pe.get("ministerio"),
                "presupuesto_2026_m$": pe.get("presupuesto_2026_m$"),
                "variacion_pct": pe.get("variacion_pct"),
                "descripcion": pe.get("descripcion") or "Ficha de evaluación de programas públicos BIPS / DIPRES."
            },
            "bajada_calle": b_mock,
            "estaciones": estaciones_bips
        }
        if pe.get("id_bips"):
            recorridos_dict[str(pe["id_bips"])] = rec_bips
        if pe.get("nombre_programa"):
            recorridos_dict[pe["nombre_programa"]] = rec_bips
            recorridos_dict[pe["nombre_programa"].casefold()] = rec_bips

    # Comparación base 2025 vs 2026
    comparacion_payload = {
        "origen": "dipres_ley_inicial",
        "motivo": "Comparación multianual con identidad de seis códigos presupuestarios DIPRES.",
        "datos": []
    }

    # Guardar en dist/data y docs/data
    archivos_json = {
        "presupuesto2027.json": presupuesto2027_payload,
        "programas.json": programas_eval,
        "servicios.json": servicios_list,
        "equivalencias.json": equivalencias_payload,
        "comparacion.json": comparacion_payload,
        "recorridos.json": recorridos_dict
    }

    for dir_destino in [DIST_DIR, DOCS_DIR]:
        for nombre, obj in archivos_json.items():
            dest = dir_destino / "data" / nombre
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
            print(f"Generado {dest} ({dest.stat().st_size:,} bytes)")

        # Copiar CSV públicos y matrices para descarga directa
        for data_file in ["programas_evaluados_dipres.csv", "costos_referencia.csv", "matriz_articulado_2026_2027.json"]:
            src = DATA_DIR / data_file
            if src.is_file():
                shutil.copyfile(src, dir_destino / "data" / data_file)

        # Generar artefactos para consumo por Agentes de IA y LLMs (llms.txt, openapi.json, prompt_agente.md)
        llms_txt_content = f"""# De la Glosa a la Calle: Presupuesto Público 2027 vs 2026

> Entiende qué cambia en el presupuesto de un programa público, revisa las fuentes y dimensiona sus montos con referencias de compras públicas.
> URL pública principal: {PUBLIC_URL}/
> Esta documentación describe el candidato exportado; la versión pública puede ser anterior.
> Repositorio GitHub: https://github.com/evegat/delaglosaalacalle

## Directrices para Agentes de Inteligencia Artificial (LLMs)
- Unidades monetarias: Miles de pesos chilenos (M$ CLP) y millones de USD según se indique.
- Fuentes oficiales:
  - Ley Inicial y Vigente 2026: Ley N° 21.796 (DIPRES).
  - Proyecto de Presupuestos 2027: Mensaje Presidencial N° 180 (Cámara de Diputadas y Diputados).
- Criterios de rigurosidad presupuestaria:
  1. Una variación presupuestaria NO demuestra por sí sola prestaciones efectivamente perdidas ni territorialidad exacta.
  2. Los programas sin contraparte identificada en 2026 tienen base NULL (no imputar falso cero).
  3. No generalizar compras de un ministerio a otro (los computadores sólo aplican a programas de tecnología escolar como Becas TIC).
  4. Endeudamiento (Artículo 3): Propone elevar el techo de deuda de US$ 17.400M a US$ 25.000M (+43,7% / +US$ 7.600M). Es una autorización máxima de endeudamiento para el ejercicio, no deuda emitida.
  5. SLEP (Artículo 40): Reitera la suspensión del traspaso de 5 SLEP (Litoral, Los Cerezos, Los Copihues, Chacabuco y Los Viñedos), la cual ya estaba vigente en 2026 bajo el Art. 41 de la Ley 21.796.

## Datasets Estructurados Disponibles (JSON y CSV)
- [Presupuesto 2027 vs 2026 (JSON)]({PUBLIC_URL}/data/presupuesto2027.json): {cobertura_presupuesto}, con base inicial 2026, vigente 2026, proyecto 2027 y variaciones. Sumas brutas de programas, no gasto público consolidado.
- [Matriz de Articulado Normativo (JSON)]({PUBLIC_URL}/data/matriz_articulado_2026_2027.json): 9 ejes normativos críticos (deuda, suspensión SLEP, cobro ejecutivo SEP con embargo, tope a honorarios, blindaje fundaciones anti Convenios, trato directo en obras, pago a proveedores, publicidad estatal y plataforma transaccional).
- [Recorridos de la Glosa a la Calle (JSON)]({PUBLIC_URL}/data/recorridos.json): Fichas de contexto institucional, mecanismo presupuestario y escenarios de magnitud; no acreditan ejecución ni impacto observado.
- [Catálogo de Programas Evaluados DIPRES (CSV)]({PUBLIC_URL}/data/programas_evaluados_dipres.csv): {len(programas_eval)} programas evaluados con código BIPS, descripción oficial y motivos de variación presupuestaria.
- [Costos de Referencia en Mercado Público (CSV)]({PUBLIC_URL}/data/costos_referencia.csv): Muestras observacionales con cuartiles P25, P50, P75 y contratos de referencia.

## Integración con Agentes y Custom GPTs
- [Especificación OpenAPI 3.1.0]({PUBLIC_URL}/openapi.json): Importable directamente como 'Action' en Custom GPTs de ChatGPT o como herramienta de consulta en frameworks de agentes.
- [Prompt de Asistente Presupuestario]({PUBLIC_URL}/prompt_agente.md): Instrucciones listas para copiar y pegar en ChatGPT, Claude o Gemini.
"""
        (dir_destino / "llms.txt").write_text(llms_txt_content, encoding="utf-8")

        openapi_spec = {
            "openapi": "3.1.0",
            "info": {
                "title": "De la Glosa a la Calle API",
                "description": "Catálogo determinista de datos abiertos del Presupuesto Público de Chile 2027 vs 2026.",
                "version": "2.0.0"
            },
            "servers": [
                {
                    "url": PUBLIC_URL,
                    "description": "Dominio público principal; verificar versión y disponibilidad del candidato publicado"
                }
            ],
            "paths": {
                "/data/presupuesto2027.json": {
                    "get": {
                        "operationId": "obtenerPresupuesto2027",
                        "summary": f"Comparativa 2026 vs 2027: {cobertura_presupuesto}",
                        "description": f"Retorna sumas brutas y detalle de {cobertura_presupuesto}, con montos inicial 2026, vigente 2026 y proyecto 2027 en miles de pesos. No representa gasto público consolidado ni prestaciones perdidas.",
                        "responses": {
                            "200": {
                                "description": "Resumen y lista de programas presupuestarios",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                },
                "/data/matriz_articulado_2026_2027.json": {
                    "get": {
                        "operationId": "obtenerMatrizArticulado",
                        "summary": "Obtiene los 9 ejes normativos del articulado (Ley 2026 vs Proyecto 2027)",
                        "description": "Contraste normativo riguroso entre la Ley N° 21.796 y el Mensaje N° 180 (endeudamiento, SLEP, SEP, honorarios, fundaciones, obras, proveedores, publicidad, transparencia).",
                        "responses": {
                            "200": {
                                "description": "Lista de ejes normativos comparados",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "array"}
                                    }
                                }
                            }
                        }
                    }
                },
                "/data/recorridos.json": {
                    "get": {
                        "operationId": "obtenerRecorridosGasto",
                        "summary": "Obtiene los recorridos de gasto desde la glosa hasta la calle",
                        "description": "Diccionario indexado por código de programa y BIPS con las 4 estaciones de ejecución fiscal y compras públicas.",
                        "responses": {
                            "200": {
                                "description": "Mapa de recorridos",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        with open(dir_destino / "openapi.json", "w", encoding="utf-8") as f:
            json.dump(openapi_spec, f, ensure_ascii=False, indent=2)

        prompt_agente_content = f"""# Prompt de Asistente Ciudadano de Presupuesto Público (P149)

Puedes copiar y pegar este prompt en **ChatGPT**, **Claude**, **Gemini** o tu agente favorito para convertirlo en un experto riguroso sobre el Presupuesto 2027:

```markdown
Eres un asistente cívico riguroso especializado en el Presupuesto Público de Chile 2027 y su comparativa frente a la Ley 2026.
Consulta los datos del proyecto 'De la Glosa a la Calle' ({PUBLIC_URL}/), revisa la autoridad y el estado de verificación registrados y respalda cada respuesta con sus fuentes. No supongas que todos los datos o escenarios tienen el mismo nivel de evidencia. Comprueba que los archivos estén disponibles en la versión pública; esta guía describe el candidato exportado, que puede no estar publicado todavía.

Instrucciones de consulta:
1. Para responder dudas de programas y cifras, consulta los datos estructurados en:
   {PUBLIC_URL}/data/presupuesto2027.json
2. Para dudas normativas y de leyes (endeudamiento, SLEP, fundaciones, honorarios), consulta:
   {PUBLIC_URL}/data/matriz_articulado_2026_2027.json
3. Reglas metodológicas obligatorias:
   - Los montos están en miles de pesos chilenos (M$ CLP).
   - Base 2026: Ley N° 21.796 (DIPRES).
   - Proyecto 2027: Mensaje Presidencial N° 180 (Cámara de Diputadas y Diputados).
   - El endeudamiento fiscal propuesto en el Art. 3 sube de US$ 17.400M a US$ 25.000M (+43,7%).
   - La suspensión de 5 SLEP (Art. 40) ya existía en 2026 (Art. 41 de Ley 21.796).
   - Una variación presupuestaria NO demuestra por sí sola servicios o prestaciones perdidas en terreno.
   - Cita siempre la fuente y el enlace de consulta de {PUBLIC_URL}/
```
"""
        (dir_destino / "prompt_agente.md").write_text(prompt_agente_content, encoding="utf-8")

    print(f"Exportación estática completada para {len(progs_2027)} programas 2027 y {len(programas_eval)} evaluados.")
    print("Artefactos para Agentes de IA generados: llms.txt, openapi.json, prompt_agente.md")

if __name__ == "__main__":
    exportar_todo()

