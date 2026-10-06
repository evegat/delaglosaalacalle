import json
import csv

csv_path = 'data/ley_inicial_vigente_programa_julio_2026.csv'
prog_2026 = {}

with open(csv_path, encoding='latin1') as f:
    reader = csv.DictReader(f, delimiter=';')
    col_cap = [k for k in reader.fieldnames if k.startswith('Cap') and 'Nombre' not in k][0]
    col_sub = [k for k in reader.fieldnames if k.startswith('Subt') and 'Nombre' not in k][0]
    col_prog = 'Programa'
    col_part = 'Partida'
    col_ini = [k for k in reader.fieldnames if 'Inicial' in k][0]
    col_vig = [k for k in reader.fieldnames if 'Vigente' in k][0]
    
    for row in reader:
        if row.get(col_part, '').strip() != '18':
            continue
        item = (row.get('Item') or '').strip()
        if item:
            continue
        sub_raw = (row.get(col_sub) or '').strip()
        if not sub_raw.isdigit() or int(sub_raw) < 21:
            continue
        moneda = (row.get('Moneda') or '').strip().casefold()
        if moneda != 'pesos':
            continue
            
        cap = (row.get(col_cap) or '').strip().zfill(2)
        prog = (row.get(col_prog) or '').strip().zfill(2)
        key = (cap, prog)
        
        ini_str = (row.get(col_ini) or '').strip().replace('.', '')
        vig_str = (row.get(col_vig) or '').strip().replace('.', '')
        
        ini = int(ini_str) if ini_str else 0
        vig = int(vig_str) if vig_str else 0
        
        if key not in prog_2026:
            prog_2026[key] = {
                'ini': 0, 'vig': 0,
                'nom_partida': (row.get('Nombre Partida') or '').strip(),
                'nom_cap': '',
                'nom_prog': (row.get('Nombre Programa') or '').strip()
            }
        prog_2026[key]['ini'] += ini
        prog_2026[key]['vig'] += vig

print('Programas 2026 Partida 18 cargados:', len(prog_2026))

json_path = 'data/filtraciones_2027/18_Vivienda.json'
with open(json_path, encoding='utf-8') as f:
    data_2027 = json.load(f)

resultados = []
tot_ini = 0
tot_vig = 0
tot_proy = 0

for cap in data_2027:
    cap_cod = str(cap.get('codigo')).strip().zfill(2)
    cap_nom = cap.get('nombre')
    for prog in cap.get('hijos', []):
        prog_cod = str(prog.get('codigo')).strip().zfill(2)
        prog_nom = prog.get('nombre')
        proy_gasto = 0
        for sub in prog.get('hijos', []):
            sub_cod = str(sub.get('codigo')).strip()
            if sub_cod.isdigit() and int(sub_cod) >= 21:
                proy_gasto += int(round(sub.get('proyecto', 0)))
                
        key = (cap_cod, prog_cod)
        info_2026 = prog_2026.get(key, {'ini': 0, 'vig': 0, 'nom_partida': 'MINISTERIO DE VIVIENDA Y URBANISMO', 'nom_cap': cap_nom, 'nom_prog': prog_nom})
        
        ini = info_2026['ini']
        vig = info_2026['vig']
        
        tot_ini += ini
        tot_vig += vig
        tot_proy += proy_gasto
        
        dif_ini = proy_gasto - ini
        pct_ini = round((proy_gasto / ini - 1) * 100, 2) if ini > 0 else None
        
        dif_vig = proy_gasto - vig
        pct_vig = round((proy_gasto / vig - 1) * 100, 2) if vig > 0 else None
        
        resultados.append({
            'codigo': f'18-{cap_cod}-{prog_cod}',
            'partida': '18',
            'capitulo': cap_cod,
            'programa': prog_cod,
            'nombre_partida': 'MINISTERIO DE VIVIENDA Y URBANISMO',
            'nombre_capitulo': cap_nom,
            'nombre_programa': prog_nom,
            'ini_2026_mclp': ini,
            'vig_2026_mclp': vig,
            'proy_2027_mclp': proy_gasto,
            'dif_vs_ini_mclp': dif_ini,
            'pct_vs_ini': pct_ini,
            'dif_vs_vig_mclp': dif_vig,
            'pct_vs_vig': pct_vig
        })

print('Total programas 2027 procesados:', len(resultados))
print(f'TOTAL PARTIDA 18: Ini: {tot_ini:,.0f} | Vig: {tot_vig:,.0f} | Proy: {tot_proy:,.0f}')
var_ini = (tot_proy / tot_ini - 1) * 100 if tot_ini else 0
var_vig = (tot_proy / tot_vig - 1) * 100 if tot_vig else 0
print(f'Variación Partida 18: {var_ini:+.2f}% vs Inicial | {var_vig:+.2f}% vs Vigente')

print('\nListado completo de los 22 programas de Partida 18 (Vivienda):')
for r in sorted(resultados, key=lambda x: x['codigo']):
    ini = r['ini_2026_mclp'] // 1000
    vig = r['vig_2026_mclp'] // 1000
    proy = r['proy_2027_mclp'] // 1000
    print(f"{r['codigo']} | {r['nombre_programa'][:35]} | Ini: ${ini:,}M | Vig: ${vig:,}M | Proy: ${proy:,}M | vs Ini: {r['pct_vs_ini']}% | vs Vig: {r['pct_vs_vig']}%")
