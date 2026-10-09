"""Script reproducible de ingesta, validación y sincronización de hitos de la Comisión Mixta de Presupuestos."""
from pathlib import Path
import json
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
HITOS_JSON = DATA_DIR / "comision_mixta_hitos.json"
DUCKDB_PATH = DATA_DIR / "presupuesto_compras_db.duckdb"

CAMPOS_OBLIGATORIOS = [
    "id", "fecha", "instancia", "partida", "partida_nombre",
    "capitulo", "capitulo_nombre", "tema_o_glosa", "orador",
    "cargo", "postura_o_decision", "estado", "bajada_calle",
    "video_url_timestamp", "acta_url"
]

def validar_hitos():
    if not HITOS_JSON.is_file():
        raise FileNotFoundError(f"No existe {HITOS_JSON}")
    
    with open(HITOS_JSON, encoding="utf-8") as f:
        hitos = json.load(f)
    
    if not isinstance(hitos, list) or len(hitos) == 0:
        raise ValueError("El archivo de hitos debe contener una lista no vacía.")
    
    ids_vistos = set()
    for idx, h in enumerate(hitos):
        for campo in CAMPOS_OBLIGATORIOS:
            if campo not in h or not str(h[campo]).strip():
                raise ValueError(f"Hito #{idx} carece del campo obligatorio '{campo}'")
        
        if h["id"] in ids_vistos:
            raise ValueError(f"ID duplicado en hitos: {h['id']}")
        ids_vistos.add(h["id"])
    
    print(f"[PASS] {len(hitos)} hitos de Comisión Mixta validados correctamente.")
    return hitos

def sincronizar_duckdb(hitos):
    if not DUCKDB_PATH.is_file():
        print("[SKIP] Base DuckDB no encontrada, manteniendo solo JSON.")
        return
    
    try:
        import duckdb
        con = duckdb.connect(str(DUCKDB_PATH))
        
        con.execute("CREATE TABLE IF NOT EXISTS comision_mixta_hitos ("
                    "id VARCHAR PRIMARY KEY, "
                    "fecha VARCHAR, "
                    "instancia VARCHAR, "
                    "partida VARCHAR, "
                    "partida_nombre VARCHAR, "
                    "capitulo VARCHAR, "
                    "capitulo_nombre VARCHAR, "
                    "programa_codigo VARCHAR, "
                    "tema_o_glosa VARCHAR, "
                    "orador VARCHAR, "
                    "cargo VARCHAR, "
                    "postura_o_decision VARCHAR, "
                    "estado VARCHAR, "
                    "bajada_calle VARCHAR, "
                    "video_url_timestamp VARCHAR, "
                    "acta_url VARCHAR)")
        
        con.execute("DELETE FROM comision_mixta_hitos")
        for h in hitos:
            con.execute("INSERT INTO comision_mixta_hitos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                h["id"], h["fecha"], h["instancia"], h["partida"], h["partida_nombre"],
                h["capitulo"], h["capitulo_nombre"], h.get("programa_codigo", ""),
                h["tema_o_glosa"], h["orador"], h["cargo"], h["postura_o_decision"],
                h["estado"], h["bajada_calle"], h["video_url_timestamp"], h["acta_url"]
            ))
        con.close()
        print(f"[PASS] {len(hitos)} hitos sincronizados en tabla comision_mixta_hitos de DuckDB.")
    except Exception as exc:
        print(f"[WARN] No se pudo sincronizar con DuckDB: {exc}")

if __name__ == "__main__":
    hitos_validados = validar_hitos()
    sincronizar_duckdb(hitos_validados)
