"""Challenger M1-2: Pruebas Empíricas de Integridad de Datos, Invariantes y Paridad Multicapa.

Verificación independiente de los cálculos oficiales y la paridad determinista:
1. Exactamente 515 programas en 33 partidas oficiales.
2. Suma de gasto bruto de programas exactamente $217.892.642.270 M$ ($217,89B).
3. Base 2026: 457 programas con variación nominal, 58 programas con NULL base (cero nunca imputado).
4. Unidades físicas: exactamente 188 programas con bajada_calle != null.
5. Dotación / Subtítulo 21: exactamente 445 programas con tiene_dotacion == true y '21' in subtitulos.
6. Artículos 3 y 40: Artículo 3 endeudamiento US$ 25.000M vs US$ 17.400M (+43,68%), Artículo 40 freno a 5 SLEP.
7. Paridad 100% multicapa: DuckDB == FastAPI (/api/presupuesto2027) == docs/data/presupuesto2027.json == dist/data/presupuesto2027.json.
"""

import json
from pathlib import Path
from contextlib import closing
import duckdb
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / 'src'))
from server import app


def test_empirico_universo_515_y_33_partidas():
    """Verifica universo estricto de 515 programas y 33 partidas."""
    docs_path = ROOT / 'docs/data/presupuesto2027.json'
    datos = json.loads(docs_path.read_text(encoding='utf-8'))
    progs = datos['programas']

    assert len(progs) == 515, f'Se esperaban 515 programas, se encontraron {len(progs)}'
    
    # Unicidad estricta de códigos presupuestarios
    codigos = [p['codigo'] for p in progs]
    assert len(codigos) == len(set(codigos)) == 515, 'Existen códigos duplicados en el universo'

    # Exactamente 33 partidas
    partidas = {p.get('partida') for p in progs if p.get('partida')}
    assert len(partidas) == 33, f'Se esperaban 33 partidas, se encontraron {len(partidas)}'
    assert '50' in partidas, 'La Partida 50 (Tesoro Público) debe estar presente'


def test_empirico_suma_bruta_217_billones():
    """Verifica la suma bruta de $217.892.642.270 M$ ($217,89B) y sus invariantes matemáticas."""
    docs_path = ROOT / 'docs/data/presupuesto2027.json'
    datos = json.loads(docs_path.read_text(encoding='utf-8'))
    progs = datos['programas']

    suma_proy = sum(p.get('proy_2027_mclp', 0) for p in progs if p.get('proy_2027_mclp') is not None)
    assert suma_proy == 217892642270, f'Suma bruta incorrecta: {suma_proy}'

    # Invariante en la sección resumen
    assert datos['totales_mclp']['proyecto_2027'] == 217892642270

    # Invariante aditiva de comparables + sin contraparte
    comp_ini = datos['comparables']['inicial']
    progs_null = [p for p in progs if p.get('ini_2026_mclp') is None]
    suma_null = sum(p['proy_2027_mclp'] for p in progs_null)
    assert comp_ini['proyecto_2027_mclp'] + suma_null == 217892642270
    assert comp_ini['base_2026_mclp'] + comp_ini['diferencia_mclp'] == comp_ini['proyecto_2027_mclp']


def test_empirico_base_2026_457_variacion_y_58_null():
    """Verifica que exactamente 457 tengan variación y 58 sean NULL sin imputar cero jamás."""
    docs_path = ROOT / 'docs/data/presupuesto2027.json'
    datos = json.loads(docs_path.read_text(encoding='utf-8'))
    progs = datos['programas']

    con_base = [p for p in progs if p.get('ini_2026_mclp') is not None]
    sin_base = [p for p in progs if p.get('ini_2026_mclp') is None]

    assert len(con_base) == 457, f'Esperados 457 con base, obtenidos {len(con_base)}'
    assert len(sin_base) == 58, f'Esperados 58 sin base, obtenidos {len(sin_base)}'

    # En los 58 sin base, el cero NUNCA es imputado
    for p in sin_base:
        assert p.get('dif_vs_ini_mclp') is None
        assert p.get('pct_vs_ini') is None
        assert p.get('estado_base_2026') == 'sin_contraparte_identificada'

    # En los 457 con base, la matemática nominal es exacta
    for p in con_base:
        ini = p['ini_2026_mclp']
        proy = p['proy_2027_mclp']
        dif = p['dif_vs_ini_mclp']
        pct = p['pct_vs_ini']
        assert dif == (proy - ini)
        if ini > 0:
            assert pct == round((proy / ini - 1) * 100, 2)
        else:
            assert pct is None


def test_empirico_tangibilidad_188_unidades_fisicas():
    """Verifica exactamente 188 programas con bajada a la calle calculada."""
    docs_path = ROOT / 'docs/data/presupuesto2027.json'
    datos = json.loads(docs_path.read_text(encoding='utf-8'))
    progs = datos['programas']

    tangibles = [p for p in progs if p.get('bajada_calle') is not None]
    assert len(tangibles) == 188, f'Esperados 188 tangibles, obtenidos {len(tangibles)}'

    for p in tangibles:
        bc = p['bajada_calle']
        assert bc['costo_unitario_clp'] > 0
        assert bc['cantidad'] > 0
        assert bc['unidad'] != ''
        assert bc['impacto_texto'] != ''
        assert bc['organismo'] != ''
        assert bc['contrato_ref'] != ''


def test_empirico_dotacion_445_subtitulo_21():
    """Verifica coherencia estricta entre subtitulo 21 y tiene_dotacion en los 515 programas."""
    docs_path = ROOT / 'docs/data/presupuesto2027.json'
    datos = json.loads(docs_path.read_text(encoding='utf-8'))
    progs = datos['programas']

    con_dotacion = [p for p in progs if p.get('tiene_dotacion') is True]
    sin_dotacion = [p for p in progs if p.get('tiene_dotacion') is False]

    assert len(con_dotacion) == 445, f'Esperados 445 con dotación, obtenidos {len(con_dotacion)}'
    assert len(sin_dotacion) == 70, f'Esperados 70 sin dotación, obtenidos {len(sin_dotacion)}'

    for p in progs:
        subs = p.get('subtitulos', [])
        dot = p.get('tiene_dotacion')
        m_pers = p.get('monto_personal_2027_mclp', 0)
        assert dot == ('21' in subs)
        if dot:
            assert m_pers > 0
        else:
            assert m_pers == 0


def test_empirico_articulos_3_y_40():
    """Verifica la matriz de articulado normativo para los Artículos 3 y 40."""
    matriz_path = ROOT / 'docs/data/matriz_articulado_2026_2027.json'
    matriz = json.loads(matriz_path.read_text(encoding='utf-8'))

    art3 = next((a for a in matriz if a.get('id') == 'art-03-deuda'), None)
    assert art3 is not None, 'Artículo 3 no encontrado en matriz'
    calc = art3['calculo']
    assert calc['base_2026_millones_usd'] == 17400
    assert calc['propuesta_2027_millones_usd'] == 25000
    assert calc['diferencia_millones_usd'] == 7600
    assert round(calc['variacion_pct'], 2) == 43.68

    art40 = next((a for a in matriz if a.get('id') == 'art-40-slep'), None)
    assert art40 is not None, 'Artículo 40 no encontrado en matriz'
    assert 'Litoral' in art40['norma_2027']
    assert 'Los Cerezos' in art40['norma_2027']
    assert 'Los Copihues' in art40['norma_2027']
    assert 'Chacabuco' in art40['norma_2027']
    assert 'Los Viñedos' in art40['norma_2027']


def test_empirico_paridad_multicapa_duckdb_fastapi_json():
    """Verifica paridad exacta entre DuckDB, FastAPI y archivos JSON."""
    db_path = ROOT / 'data/presupuesto_compras_db.duckdb'
    assert db_path.is_file(), 'Base DuckDB no encontrada'

    # 1. DuckDB consulta directa
    with closing(duckdb.connect(str(db_path), read_only=True)) as con:
        db_count = con.execute('SELECT COUNT(*) FROM programas_2026_2027').fetchone()[0]
        db_sum = con.execute('SELECT SUM(proy_2027_mclp) FROM programas_2026_2027').fetchone()[0]
        assert db_count == 515
        assert db_sum == 217892642270

    # 2. FastAPI endpoint
    client = TestClient(app)
    resp = client.get('/api/presupuesto2027')
    assert resp.status_code == 200
    api_data = resp.json()
    assert len(api_data['programas']) == 515
    assert api_data['totales_mclp']['proyecto_2027'] == 217892642270

    # 3. JSON files
    docs_data = json.loads((ROOT / 'docs/data/presupuesto2027.json').read_text(encoding='utf-8'))
    dist_data = json.loads((ROOT / 'dist/data/presupuesto2027.json').read_text(encoding='utf-8'))

    # Cotejo exhaustivo programa a programa
    api_by_code = {p['codigo']: p for p in api_data['programas']}
    docs_by_code = {p['codigo']: p for p in docs_data['programas']}
    dist_by_code = {p['codigo']: p for p in dist_data['programas']}

    assert set(api_by_code.keys()) == set(docs_by_code.keys()) == set(dist_by_code.keys())

    for code, p_api in api_by_code.items():
        p_docs = docs_by_code[code]
        p_dist = dist_by_code[code]
        assert json.dumps(p_api, sort_keys=True) == json.dumps(p_docs, sort_keys=True)
        assert json.dumps(p_docs, sort_keys=True) == json.dumps(p_dist, sort_keys=True)
