"""Integra la Partida 16 (Salud) al dataset consolidado de P149."""
import json
from pathlib import Path
from cruce_salud_16 import resultados as progs_salud

# 1. Cargar dataset actual
json_path = Path("data/comparativa_programas_2026_2027.json")
with open(json_path, encoding="utf-8") as f:
    existentes = json.load(f)

# Filtrar para no duplicar si ya existe partida 16
filtrados = [p for p in existentes if p.get("partida") != "16"]

# Agregar los 71 programas de Salud
todos = filtrados + progs_salud

print(f"Programas existentes sin Salud: {len(filtrados)}")
print(f"Programas nuevos de Salud: {len(progs_salud)}")
print(f"Nuevo total consolidado: {len(todos)} programas")

# Guardar en deploy y root
for p_out in [
    Path("data/comparativa_programas_2026_2027.json"),
    Path("../data/comparativa_programas_2026_2027.json")
]:
    with open(p_out, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)
    print(f"Guardado exitoso en {p_out}")

# Estadísticas globales consolidadas
tot_ini = sum(p["ini_2026_mclp"] for p in todos)
tot_vig = sum(p["vig_2026_mclp"] for p in todos)
tot_proy = sum(p["proy_2027_mclp"] for p in todos)

print(f"\n--- TOTAL CARTERA P149 (6 PARTIDAS: 05, 09, 16, 18, 29, 31) ---")
print(f"Total Inicial 2026:  ${tot_ini:,.0f} M$")
print(f"Total Vigente 2026:  ${tot_vig:,.0f} M$")
print(f"Total Proyecto 2027: ${tot_proy:,.0f} M$")
var_ini = (tot_proy / tot_ini - 1) * 100 if tot_ini else 0
var_vig = (tot_proy / tot_vig - 1) * 100 if tot_vig else 0
print(f"Variación Cartera: {var_ini:+.2f}% vs Inicial | {var_vig:+.2f}% vs Vigente")
