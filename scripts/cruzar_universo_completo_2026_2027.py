import csv
import json
import hashlib
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

import sys
sys.path.insert(0, str(BASE_DIR / "src"))
from presupuesto_ciudadano import preparar_programas

# 1. Cargar catálogo oficial 2027 desde XML procesado
with open(DATA_DIR / "catalogo_programas_2027_dipres.json", encoding="utf-8") as f:
    programas_2027 = json.load(f)

# Hash de XML
xml_bytes = (DATA_DIR / "proyecto_presupuesto_2027_dipres_oficial.xml").read_bytes()
xml_sha = hashlib.sha256(xml_bytes).hexdigest()

# 2. Cargar Ley Inicial y Vigente 2026
csv_2026_path = BASE_DIR.parent / "data/ley_inicial_vigente_programa_julio_2026.csv"
csv_2026_bytes = csv_2026_path.read_bytes()
csv_2026_sha = hashlib.sha256(csv_2026_bytes).hexdigest()

with open(csv_2026_path, encoding="utf-8-sig") as f:
    rows_2026 = list(csv.DictReader(f, delimiter=";"))

progs_2026 = {}
for r in rows_2026:
    campos = list(r)
    cap = next(k for k in campos if k.startswith("Cap") and "Nombre" not in k)
    sub = next(k for k in campos if k.startswith("Subt") and "Nombre" not in k)
    asig = next(k for k in campos if k.startswith("Asign") and "Nombre" not in k)
    item = r.get("Item", "").strip()
    
    if r["Moneda"].casefold() != "pesos" or item or r[asig].strip():
        continue
    if not r[sub].isdigit() or not 21 <= int(r[sub]) <= 35:
        continue
        
    p = r["Partida"].strip().zfill(2)
    c = r[cap].strip().zfill(2)
    pr = r["Programa"].strip().zfill(2)
    code = f"{p}-{c}-{pr}"
    
    b = progs_2026.setdefault(code, {
        "ini": 0, "vig": 0,
        "nombre_partida": r["Nombre Partida"].strip(),
        "nombre_capitulo": r["Nombre Cap\xedtulo"].strip(),
        "nombre_programa": r["Nombre Programa"].strip(),
    })
    
    raw_ini = r["Monto Ley Inicial"].strip().replace(".", "")
    raw_vig = r["Monto Ley Vigente a Julio"].strip().replace(".", "")
    if raw_ini and b["ini"] is not None:
        b["ini"] += int(raw_ini)
    if raw_vig and b["vig"] is not None:
        b["vig"] += int(raw_vig)

# 3. Cruzar los 515 programas de 2027
consolidados = []
nuevos_sin_base = 0
coincidentes = 0

fuente_2026_meta = {
    "archivo": "ley_inicial_vigente_programa_julio_2026.csv",
    "sha256": csv_2026_sha,
    "tipo": "ley_inicial_y_vigente_dipres"
}

fuente_2027_meta = {
    "archivo": "proyecto_presupuesto_2027_dipres_oficial.xml",
    "sha256": xml_sha,
    "tipo": "proyecto_ley_dipres_contraloria"
}

for p in programas_2027:
    code = p["codigo"]
    b26 = progs_2026.get(code)
    proy_mclp = p["proy_2027_mclp"]
    
    if b26 is not None:
        coincidentes += 1
        ini = b26["ini"]
        vig = b26["vig"]
        comparabilidad = "comparable"
        estado_base = "disponible"
    else:
        nuevos_sin_base += 1
        ini = None
        vig = None
        comparabilidad = "sin_contraparte_identificada"
        estado_base = "sin_contraparte_identificada"

    # Cálculos deterministas
    dif_ini = (proy_mclp - ini) if (ini is not None) else None
    pct_ini = round((proy_mclp / ini - 1) * 100, 2) if (dif_ini is not None and ini > 0) else None
    
    dif_vig = (proy_mclp - vig) if (vig is not None) else None
    pct_vig = round((proy_mclp / vig - 1) * 100, 2) if (dif_vig is not None and vig > 0) else None

    # Variación real deflactada estimada (si la inflación proyecto/ley está calibrada; por ahora determinista None si no hay deflactor oficial por glosa)
    var_real = None

    row = {
        "codigo": code,
        "partida": p["partida"],
        "capitulo": p["capitulo"],
        "programa": p["programa"],
        "nombre_partida": p["nombre_partida"],
        "nombre_capitulo": p["nombre_capitulo"],
        "nombre_programa": p["nombre_programa"],
        "ini_2026_mclp": ini,
        "vig_2026_mclp": vig,
        "proy_2027_mclp": proy_mclp,
        "proy_2027_usd": p.get("proy_2027_usd", 0),
        "dif_vs_ini_mclp": dif_ini,
        "pct_vs_ini": pct_ini,
        "dif_vs_vig_mclp": dif_vig,
        "pct_vs_vig": pct_vig,
        "variacion_real_pct": var_real,
        "comparabilidad_institucional": comparabilidad,
        "nombre_original_importado": None,
        "estado_base_2026": estado_base,
        "fuente_2026": fuente_2026_meta if b26 else None,
        "fuente_2027": fuente_2027_meta
    }
    consolidados.append(row)

# Aplicar motor de bajada a la calle y preparación
consolidados = preparar_programas(consolidados)

print(f"Total programas 2027: {len(consolidados)}")
print(f"  Programas con base 2026 identificada: {coincidentes}")
print(f"  Programas nuevos / sin base 2026 (NULL explícito): {nuevos_sin_base}")

# Guardar en JSON canónico
out_json = DATA_DIR / "comparativa_programas_2026_2027_completa.json"
out_json.write_text(json.dumps(consolidados, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Guardado en {out_json}")
