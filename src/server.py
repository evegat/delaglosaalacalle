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

import os
import sqlite3
import datetime
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import duckdb
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "presupuesto_compras_db.duckdb"
SQLITE_PATH = DATA_DIR / "preguntas_ciudadanas.sqlite3"

# Fecha objetivo: Lunes 05 de Octubre 2026, 08:00 AM Hora de Chile (UTC-3)
OBJETIVO_LUNES = datetime.datetime(2026, 10, 5, 8, 0, 0)

app = FastAPI(
    title="De la Glosa a la Calle API",
    description="Observatorio Cívico de Gasto Fiscal y Compras Públicas",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar base de datos SQLite para preguntas
def init_sqlite():
    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    cur.execute("""
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
    conn.commit()
    conn.close()

init_sqlite()

class PreguntaInput(BaseModel):
    pregunta: str
    comuna: Optional[str] = None
    contacto: Optional[str] = None

@app.get("/api/countdown")
def get_countdown():
    ahora = datetime.datetime.now()
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
        "mensaje": "Cuenta regresiva para la liberación oficial de las 29 partidas restantes del Presupuesto 2027 (Lunes 5 de octubre a las 08:00 AM)"
    }

@app.post("/api/preguntas")
def crear_pregunta(payload: PreguntaInput):
    texto = payload.pregunta.strip()
    if len(texto) < 4:
        raise HTTPException(status_code=400, detail="La pregunta es demasiado corta.")
    
    # Buscar si hay coincidencia semántica en los programas de DIPRES
    match_programa = None
    motivo_hacienda = None
    
    try:
        con = duckdb.connect(str(DB_PATH), read_only=True)
        # Búsqueda simple de palabras clave
        palabras = [w for w in texto.lower().split() if len(w) > 3]
        for p in palabras:
            res = con.execute("""
                SELECT nombre_programa, motivo_variacion_presupuestaria, variacion_presupuesto_2025_2026_pct
                FROM programas_evaluados_dipres
                WHERE LOWER(nombre_programa) LIKE ? OR LOWER(motivo_variacion_presupuestaria) LIKE ?
                LIMIT 1
            """, [f"%{p}%", f"%{p}%"]).fetchone()
            if res:
                match_programa = f"{res[0]} (Variación: {res[2]}%)"
                motivo_hacienda = res[1]
                break
        con.close()
    except Exception as e:
        pass
    
    # Persistir en SQLite
    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO preguntas_ciudadanas (pregunta, comuna, contacto, programa_coincidente, motivo_hacienda, respondida_en_vivo)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (texto, payload.comuna, payload.contacto, match_programa, motivo_hacienda, match_programa is not None))
    qid = cur.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "ok": True,
        "id": qid,
        "match_encontrado": match_programa is not None,
        "programa": match_programa,
        "motivo_hacienda": motivo_hacienda,
        "mensaje_respuesta": (
            f"¡Detectamos datos preliminares! Sobre {match_programa}: El Ministerio de Hacienda señala: '{motivo_hacienda}'."
            if match_programa else
            "Pregunta registrada con éxito. La priorizaremos para el cruce de datos este lunes a las 08:00 AM."
        )
    }

@app.get("/api/preguntas")
def listar_preguntas(limit: int = 10):
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, fecha, pregunta, comuna, programa_coincidente, respondida_en_vivo
        FROM preguntas_ciudadanas
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/api/programas")
def listar_programas(q: Optional[str] = None):
    con = duckdb.connect(str(DB_PATH), read_only=True)
    if q:
        query_sql = """
            SELECT * FROM programas_evaluados_dipres
            WHERE LOWER(ministerio) LIKE ? OR LOWER(nombre_programa) LIKE ? OR LOWER(motivo_variacion_presupuestaria) LIKE ?
            ORDER BY variacion_presupuesto_2025_2026_pct ASC
        """
        wild = f"%{q.lower()}%"
        df = con.execute(query_sql, [wild, wild, wild]).fetchdf()
    else:
        df = con.execute("SELECT * FROM programas_evaluados_dipres ORDER BY variacion_presupuesto_2025_2026_pct ASC").fetchdf()
    con.close()
    return df.to_dict(orient="records")

# Montar frontend estático si existe dist/
if DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server:app", host="0.0.0.0", port=8088, reload=False)
