import csv
from collections import defaultdict
from pathlib import Path

csv_path = Path("data/proyecto_presupuesto_2027_dipres_oficial.csv")
with open(csv_path, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter=";")
    rows = list(reader)

print(f"Total filas: {len(rows)}")
partidas = set()
capitulos = set()
programas = set()
gastos_sub = defaultdict(int)
totales_programa = defaultdict(int)

# Detectar columna Item/Ítem
item_col = [c for c in reader.fieldnames if "tem" in c.lower() or "item" in c.lower()][0]

for r in rows:
    p = r["Partida"].strip().zfill(2)
    c = r["Capitulo"].strip().zfill(2)
    pr = r["Programa"].strip().zfill(2)
    code = f"{p}-{c}-{pr}"
    
    partidas.add(p)
    capitulos.add(f"{p}-{c}")
    programas.add(code)
    
    sub = r["Subtitulo"].strip()
    item = r[item_col].strip()
    asig = r["Asignacion"].strip()
    
    try:
        monto = int(r["Monto Pesos"].strip())
    except ValueError:
        monto = 0
        
    # Nivel subtitulo directo: item '00' y asig '000'
    if item == "00" and asig == "000":
        if sub.isdigit() and int(sub) >= 21:
            gastos_sub[sub] += monto
            totales_programa[code] += monto

print(f"Partidas unicas: {len(partidas)}: {sorted(partidas)}")
print(f"Capitulos unicos: {len(capitulos)}")
print(f"Programas unicos: {len(programas)}")
print(f"\nSuma total de gastos presupuestarios 2027 (Subtitulos 21 a 35): {sum(gastos_sub.values()):,} Miles de $")
print("\nDesglose por subtitulo a nivel nacional (Miles de $):")
for s in sorted(gastos_sub.keys()):
    print(f"  Subtitulo {s}: {gastos_sub[s]:,} Miles de $")
