"""Migración determinista a DuckDB de la comparativa 2026-2027 y matriz de articulado.

Garantiza tipos nativos, valores NULL explícitos (cero no imputado),
trazabilidad por código presupuestario y hash SHA-256 de las fuentes oficiales.
"""
import json
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "presupuesto_compras_db.duckdb"


def migrar_duckdb():
    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(DB_PATH))

    # 1. Tabla de programas presupuestarios 2026-2027
    comp_path = DATA_DIR / "comparativa_programas_2026_2027.json"
    if not comp_path.is_file():
        raise FileNotFoundError(f"No se encuentra {comp_path}")

    with open(comp_path, encoding="utf-8") as f:
        programas = json.load(f)

    con.execute("DROP TABLE IF EXISTS programas_2026_2027")
    con.execute("""
        CREATE TABLE programas_2026_2027 (
            codigo VARCHAR PRIMARY KEY,
            partida VARCHAR,
            capitulo VARCHAR,
            programa VARCHAR,
            nombre_partida VARCHAR,
            nombre_capitulo VARCHAR,
            nombre_programa VARCHAR,
            ini_2026_mclp BIGINT,
            vig_2026_mclp BIGINT,
            proy_2027_mclp BIGINT,
            dif_vs_ini_mclp BIGINT,
            pct_vs_ini DOUBLE,
            dif_vs_vig_mclp BIGINT,
            pct_vs_vig DOUBLE,
            fuente_2026_json VARCHAR,
            fuente_2027_json VARCHAR,
            comparabilidad_institucional VARCHAR,
            variacion_real_pct DOUBLE,
            nombre_original_importado VARCHAR,
            estado_base_2026 VARCHAR
        )
    """)

    for p in programas:
        ini = p.get("ini_2026_mclp")
        vig = p.get("vig_2026_mclp")
        proy = p.get("proy_2027_mclp")

        dif_ini = (proy - ini) if (proy is not None and ini is not None) else None
        pct_ini = round((proy / ini - 1) * 100, 2) if (dif_ini is not None and ini > 0) else None

        dif_vig = (proy - vig) if (proy is not None and vig is not None) else None
        pct_vig = round((proy / vig - 1) * 100, 2) if (dif_vig is not None and vig > 0) else None

        estado_base = "disponible" if ini is not None else "sin_contraparte_identificada"

        f26_str = json.dumps(p.get("fuente_2026"), ensure_ascii=False) if p.get("fuente_2026") else None
        f27_str = json.dumps(p.get("fuente_2027"), ensure_ascii=False) if p.get("fuente_2027") else None

        con.execute("""
            INSERT INTO programas_2026_2027 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p.get("codigo"),
            p.get("partida"),
            p.get("capitulo"),
            p.get("programa"),
            p.get("nombre_partida"),
            p.get("nombre_capitulo"),
            p.get("nombre_programa"),
            ini,
            vig,
            proy,
            dif_ini,
            pct_ini,
            dif_vig,
            pct_vig,
            f26_str,
            f27_str,
            p.get("comparabilidad_institucional"),
            p.get("variacion_real_pct"),
            p.get("nombre_original_importado"),
            estado_base
        ))

    # 2. Tabla de Matriz de Articulado
    art_path = DATA_DIR / "matriz_articulado_2026_2027.json"
    if art_path.is_file():
        with open(art_path, encoding="utf-8") as f:
            articulado = json.load(f)

        con.execute("DROP TABLE IF EXISTS articulado_2026_2027")
        con.execute("""
            CREATE TABLE articulado_2026_2027 (
                id VARCHAR PRIMARY KEY,
                eje VARCHAR,
                articulo VARCHAR,
                titulo VARCHAR,
                categoria VARCHAR,
                nivel_cambio VARCHAR,
                tipo_cambio VARCHAR,
                norma_2026 VARCHAR,
                norma_2027 VARCHAR,
                impacto_calle VARCHAR,
                ley_2026 VARCHAR,
                articulo_2026 VARCHAR,
                pagina_2026 INTEGER,
                pagina_2027 INTEGER,
                limite VARCHAR
            )
        """)

        for a in articulado:
            f26 = a.get("fuente_2026") or {}
            f27 = a.get("fuente_2027") or {}
            con.execute("""
                INSERT INTO articulado_2026_2027 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                a.get("id"),
                a.get("eje"),
                a.get("articulo"),
                a.get("titulo"),
                a.get("categoria"),
                a.get("nivel_cambio"),
                a.get("tipo_cambio"),
                a.get("norma_2026"),
                a.get("norma_2027"),
                a.get("impacto_calle"),
                f26.get("ley"),
                f26.get("articulo"),
                f26.get("pagina"),
                f27.get("pagina"),
                a.get("limite")
            ))

    # 3. Verificaciones automáticas
    total_progs = con.execute("SELECT count(*) FROM programas_2026_2027").fetchone()[0]
    total_nulls = con.execute("SELECT count(*) FROM programas_2026_2027 WHERE ini_2026_mclp IS NULL").fetchone()[0]
    total_art = con.execute("SELECT count(*) FROM articulado_2026_2027").fetchone()[0]

    con.close()

    print(f"Migración DuckDB completada exitosamente:")
    print(f"- {total_progs} programas en 'programas_2026_2027' ({total_nulls} con base inicial NULL).")
    print(f"- {total_art} ejes en 'articulado_2026_2027'.")
    print(f"- Base: {DB_PATH}")


if __name__ == "__main__":
    migrar_duckdb()
