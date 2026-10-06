"""Descarga y cruce metodológico de la Partida 16 (Salud) para P149."""
import json
import csv
import urllib.request
from pathlib import Path

# 1. Descargar JSON oficial 2027 de Salud
url = "https://presupuestokast.cl/datos/ministerio/16.json"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
print("Descargando Partida 16 (Salud) desde presupuestokast.cl...")
content = urllib.request.urlopen(req).read().decode("utf-8")
data_2027 = json.loads(content)

# Guardar respaldos locales
for out_p in [
    Path("data/filtraciones_2027/16_Salud.json"),
    Path("../data/filtraciones_2027/16_Salud.json")
]:
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(content, encoding="utf-8")
    print(f"Guardado respaldo en {out_p}")

# 2. Cargar Ley Inicial y Vigente 2026 desde CSV DIPRES
csv_path = Path("data/ley_inicial_vigente_programa_julio_2026.csv")
if not csv_path.exists():
    csv_path = Path("../data/ley_inicial_vigente_programa_julio_2026.csv")

prog_2026 = {}
with open(csv_path, encoding="latin1") as f:
    reader = csv.DictReader(f, delimiter=";")
    col_cap = [k for k in reader.fieldnames if k.startswith("Cap") and "Nombre" not in k][0]
    col_sub = [k for k in reader.fieldnames if k.startswith("Subt") and "Nombre" not in k][0]
    col_prog = "Programa"
    col_part = "Partida"
    col_ini = [k for k in reader.fieldnames if "Inicial" in k][0]
    col_vig = [k for k in reader.fieldnames if "Vigente" in k][0]
    
    for row in reader:
        if row.get(col_part, "").strip() != "16":
            continue
        item = (row.get("Item") or "").strip()
        if item:
            continue
        sub_raw = (row.get(col_sub) or "").strip()
        if not sub_raw.isdigit() or int(sub_raw) < 21:
            continue
        moneda = (row.get("Moneda") or "").strip().casefold()
        if moneda != "pesos":
            continue
            
        cap = (row.get(col_cap) or "").strip().zfill(2)
        prog = (row.get(col_prog) or "").strip().zfill(2)
        key = (cap, prog)
        
        ini_str = (row.get(col_ini) or "").strip().replace(".", "")
        vig_str = (row.get(col_vig) or "").strip().replace(".", "")
        
        ini = int(ini_str) if ini_str else 0
        vig = int(vig_str) if vig_str else 0
        
        if key not in prog_2026:
            prog_2026[key] = {
                "ini": 0, "vig": 0,
                "nom_partida": (row.get("Nombre Partida") or "").strip(),
                "nom_cap": "",
                "nom_prog": (row.get("Nombre Programa") or "").strip()
            }
        prog_2026[key]["ini"] += ini
        prog_2026[key]["vig"] += vig

print(f"Programas 2026 Partida 16 cargados desde CSV DIPRES: {len(prog_2026)}")

# 3. Cruzar cada programa de Salud 2027
resultados = []
tot_ini = 0
tot_vig = 0
tot_proy = 0

for cap in data_2027:
    cap_cod = str(cap.get("codigo")).strip().zfill(2)
    cap_nom = cap.get("nombre")
    for prog in cap.get("hijos", []):
        prog_cod = str(prog.get("codigo")).strip().zfill(2)
        prog_nom = prog.get("nombre")
        proy_gasto = 0
        for sub in prog.get("hijos", []):
            sub_cod = str(sub.get("codigo")).strip()
            if sub_cod.isdigit() and int(sub_cod) >= 21:
                proy_gasto += int(round(sub.get("proyecto", 0)))
                
        key = (cap_cod, prog_cod)
        info_2026 = prog_2026.get(key, {
            "ini": 0, "vig": 0,
            "nom_partida": "MINISTERIO DE SALUD",
            "nom_cap": cap_nom,
            "nom_prog": prog_nom
        })
        
        ini = info_2026["ini"]
        vig = info_2026["vig"]
        
        tot_ini += ini
        tot_vig += vig
        tot_proy += proy_gasto
        
        dif_ini = proy_gasto - ini
        pct_ini = round((proy_gasto / ini - 1) * 100, 2) if ini > 0 else None
        
        dif_vig = proy_gasto - vig
        pct_vig = round((proy_gasto / vig - 1) * 100, 2) if vig > 0 else None
        
        resultados.append({
            "codigo": f"16-{cap_cod}-{prog_cod}",
            "partida": "16",
            "capitulo": cap_cod,
            "programa": prog_cod,
            "nombre_partida": "MINISTERIO DE SALUD",
            "nombre_capitulo": cap_nom,
            "nombre_programa": prog_nom,
            "ini_2026_mclp": ini,
            "vig_2026_mclp": vig,
            "proy_2027_mclp": proy_gasto,
            "dif_vs_ini_mclp": dif_ini,
            "pct_vs_ini": pct_ini,
            "dif_vs_vig_mclp": dif_vig,
            "pct_vs_vig": pct_vig
        })

print(f"Total programas 2027 de Salud procesados: {len(resultados)}")
print(f"TOTAL PARTIDA 16 (Salud): Ini: ${tot_ini:,.0f}M | Vig: ${tot_vig:,.0f}M | Proy: ${tot_proy:,.0f}M")
var_ini = (tot_proy / tot_ini - 1) * 100 if tot_ini else 0
var_vig = (tot_proy / tot_vig - 1) * 100 if tot_vig else 0
print(f"Variación Global Salud: {var_ini:+.2f}% vs Inicial | {var_vig:+.2f}% vs Vigente")

# Mostrar principales recortes y aumentos
print("\n--- TOP 5 RECORTES EN SALUD (vs Inicial) ---")
recortes = sorted([r for r in resultados if r["dif_vs_ini_mclp"] < 0], key=lambda x: x["dif_vs_ini_mclp"])
for r in recortes[:5]:
    print(f"{r['codigo']} | {r['nombre_programa'][:40]} | Ini: ${r['ini_2026_mclp']:,}M | Proy: ${r['proy_2027_mclp']:,}M | Dif: ${r['dif_vs_ini_mclp']:,}M ({r['pct_vs_ini']}%)")

print("\n--- TOP 5 AUMENTOS EN SALUD (vs Inicial) ---")
aumentos = sorted([r for r in resultados if r["dif_vs_ini_mclp"] > 0], key=lambda x: -x["dif_vs_ini_mclp"])
for r in aumentos[:5]:
    print(f"{r['codigo']} | {r['nombre_programa'][:40]} | Ini: ${r['ini_2026_mclp']:,}M | Proy: ${r['proy_2027_mclp']:,}M | Dif: +${r['dif_vs_ini_mclp']:,}M (+{r['pct_vs_ini']}%)")
