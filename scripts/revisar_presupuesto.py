"""Revisión idempotente desde CSV 2026 y evidencia auditada de cada total 2027.

No reinterpreta un PDF ambiguo ni acepta silenciosamente archivos modificados.
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'src'))
from presupuesto_ciudadano import preparar_programas


def generar_candidato(datos, filas_2026, evidencia):
    if len({r['codigo'] for r in datos}) != len(datos):
        raise ValueError('Códigos de programa duplicados')
    bases = {}
    detalle = set()
    for r in filas_2026:
        campos = list(r)
        cap = next(k for k in campos if k.startswith('Cap') and 'Nombre' not in k)
        sub = next(k for k in campos if k.startswith('Subt') and 'Nombre' not in k)
        asig = next(k for k in campos if k.startswith('Asign') and 'Nombre' not in k)
        if r['Moneda'].casefold() != 'pesos' or r['Item'].strip() or r[asig].strip():
            continue
        if not r[sub].isdigit() or not 21 <= int(r[sub]) <= 35:
            continue
        code = '-'.join(r[k].strip().zfill(2) for k in ('Partida', cap, 'Programa'))
        if (code, r[sub]) in detalle:
            raise ValueError(f'Subtítulo duplicado: {code}/{r[sub]}')
        detalle.add((code, r[sub]))
        b = bases.setdefault(code, {'ini': 0, 'vig': 0})
        for field, name in [('Monto Ley Inicial', 'ini'), ('Monto Ley Vigente a Julio', 'vig')]:
            raw = r[field].strip().replace('.', '')
            if not raw or b[name] is None:
                b[name] = None
            else:
                b[name] += int(raw)
    result = []
    for old in datos:
        r = dict(old)
        e = evidencia['programas'].get(r['codigo'])
        if e is None:
            raise ValueError(f"Sin evidencia 2027: {r['codigo']}")
        if r['proy_2027_mclp'] not in (e['monto_previo_mclp'], e['monto_contrastado_mclp']):
            raise ValueError(f"Monto nuevo no revisado: {r['codigo']}")
        b = bases.get(r['codigo'])
        if b is None and '(Nuevo/Reestructurado)' in r.get('nombre_programa', ''):
            r['nombre_original_importado'] = r['nombre_programa']
            r['nombre_programa'] = r['nombre_programa'].replace(
                '(Nuevo/Reestructurado)', '· denominación pendiente de cotejo')
        r['ini_2026_mclp'] = b['ini'] if b else None
        r['vig_2026_mclp'] = b['vig'] if b else None
        r['proy_2027_mclp'] = e['monto_contrastado_mclp']
        r['fuente_2026'] = evidencia['fuente_2026']
        r['fuente_2027'] = e['fuente']
        r['comparabilidad_institucional'] = 'pendiente_cotejo_de_perimetros'
        r['variacion_real_pct'] = None
        result.append(r)
    result = preparar_programas(result)
    for r in result:
        r.pop('bajada_calle', None)
    return result


def regenerar():
    data_path = BASE / 'data/comparativa_programas_2026_2027.json'
    manifest = json.loads((BASE/'data/verificacion_presupuestos_20261006.json').read_text(encoding='utf-8'))
    for filename, expected in manifest['hashes_originales'].items():
        p = BASE.parent / 'data' / filename
        if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Fuente modificada: {filename}; reauditar antes de aceptar')
    csv_path = BASE.parent / 'data/ley_inicial_vigente_programa_julio_2026.csv'
    with csv_path.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f, delimiter=';'))
    result = generar_candidato(json.loads(data_path.read_text(encoding='utf-8')), rows, manifest)
    content = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    data_path.write_text(content, encoding='utf-8')
    (BASE.parent/'data'/data_path.name).write_text(content, encoding='utf-8')
    print(f'Candidato revisado: {len(result)} programas; {sum(r["ini_2026_mclp"] is None for r in result)} bases ausentes. Sin publicación.')


if __name__ == '__main__':
    regenerar()
