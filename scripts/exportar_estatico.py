"""
Exportador de artefactos estáticos para GitHub Pages y CDN.
Genera los archivos JSON completos para funcionamiento 100% offline y estático en docs/ y dist/.
"""
import json
import csv
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DIST_DIR = BASE_DIR / "dist"
DOCS_DIR = BASE_DIR / "docs"

# Importar motor de bajada a la calle
import sys
sys.path.insert(0, str(BASE_DIR / "src"))
from bajada_calle import calcular_bajada_calle

def exportar_todo():
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DIST_DIR / "data").mkdir(exist_ok=True)
    (DOCS_DIR / "data").mkdir(exist_ok=True)

    # 1. Cargar comparativa 2026-2027
    comp_path = DATA_DIR / "comparativa_programas_2026_2027.json"
    with open(comp_path, encoding="utf-8") as f:
        progs_2027 = json.load(f)

    # Calcular bajada a la calle para cada programa
    for p in progs_2027:
        p["bajada_calle"] = calcular_bajada_calle(p)

    tot_ini = sum(p.get("ini_2026_mclp", 0) for p in progs_2027)
    tot_vig = sum(p.get("vig_2026_mclp", 0) for p in progs_2027)
    tot_proy = sum(p.get("proy_2027_mclp", 0) for p in progs_2027)

    presupuesto2027_payload = {
        "total_programas": len(progs_2027),
        "totales_mclp": {
            "inicial_2026": tot_ini,
            "vigente_2026": tot_vig,
            "proyecto_2027": tot_proy,
            "dif_vs_ini": tot_proy - tot_ini,
            "dif_vs_vig": tot_proy - tot_vig
        },
        "programas": progs_2027
    }

    # 2. Cargar catálogo de programas evaluados DIPRES
    prog_eval_path = DATA_DIR / "programas_evaluados_dipres.csv"
    programas_eval = []
    servicios_set = set()
    if prog_eval_path.is_file():
        with open(prog_eval_path, encoding="latin1") as f:
            reader = csv.DictReader(f)
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
        with open(costos_path, encoding="latin1") as f:
            reader = csv.DictReader(f)
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
        bajada = p.get("bajada_calle")
        estaciones = [
            {
                "estacion": 1,
                "fase": "Origen Fiscal",
                "titulo": p.get("nombre_partida") or f"Partida {p.get('partida')}",
                "detalle": f"Capítulo: {p.get('nombre_capitulo')} · Programa: {p.get('nombre_programa')}",
                "tipo": "institucional"
            },
            {
                "estacion": 2,
                "fase": "Mecanismo Presupuestario",
                "titulo": f"Presupuesto 2027: ${p.get('proy_2027_mclp', 0):,} M$",
                "detalle": f"Variación vs Inicial 2026: {p.get('pct_vs_ini')}% (Dif: ${p.get('dif_vs_ini_mclp', 0):,} M$)",
                "regla_ejecucion": "Ley de Presupuestos del Sector Público",
                "tipo": "normativo"
            },
            {
                "estacion": 3,
                "fase": "Gestión y Compras Públicas",
                "titulo": bajada["organismo"] if bajada else (p.get("nombre_capitulo") or "Organismo Ejecutor"),
                "detalle": f"Referencia: {bajada['contrato_ref']}" if bajada else "Convenio de Transferencia / Licitación Pública",
                "tipo": "operacional"
            },
            {
                "estacion": 4,
                "fase": "En la Calle",
                "titulo": bajada["impacto_texto"] if bajada else "Prestaciones territoriales y ciudadanas",
                "costo_unitario_referencia": bajada["costo_unitario_clp"] if bajada else None,
                "dilema_calle": bajada["dilema"] if bajada else "Impacto en lista de espera y cobertura directa a beneficiarios en el territorio.",
                "tipo": "calle"
            }
        ]
        rec_obj = {
            "programa": {
                "nombre_programa": p.get("nombre_programa"),
                "servicio": p.get("nombre_capitulo"),
                "ministerio": p.get("nombre_partida"),
                "presupuesto_2026_m$": p.get("ini_2026_mclp"),
                "variacion_pct": p.get("pct_vs_ini"),
                "descripcion": f"Programa presupuestario oficial {p.get('codigo')} ({p.get('nombre_partida')}), analizado en la comparativa de la Ley de Presupuestos."
            },
            "bajada_calle": bajada,
            "estaciones": estaciones
        }
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

    print(f"Exportación estática completada para {len(progs_2027)} programas 2027 y {len(programas_eval)} evaluados.")

if __name__ == "__main__":
    exportar_todo()
