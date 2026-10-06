import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def imports(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'src'))


def test_cero_no_cambia_silenciosamente_base_equivalencia():
    from bajada_calle import calcular_bajada_calle
    p = {'partida': '09', 'nombre_programa': 'Becas TIC',
         'dif_vs_ini_mclp': 0, 'dif_vs_vig_mclp': -600000}
    assert calcular_bajada_calle(p) is None


def test_equivalencia_exige_base_disponible_y_declara_costo_estimado():
    from bajada_calle import calcular_bajada_calle
    p = {'partida': '09', 'nombre_programa': 'Becas TIC',
         'dif_vs_ini_mclp': None, 'dif_vs_vig_mclp': -600000}
    assert calcular_bajada_calle(p) is None
    b = calcular_bajada_calle(p, base='vigente')
    assert b['base_comparacion'] == 'vigente'
    assert b['estado_costo'] == 'referencia_no_verificada'
    assert 'no demuestra' in b['limite_metodologico']


def test_resumen_no_resta_poblaciones_distintas():
    from presupuesto_ciudadano import resumen_presupuestario
    rows = [
        {'ini_2026_mclp': 100, 'vig_2026_mclp': 150, 'proy_2027_mclp': 200},
        {'ini_2026_mclp': None, 'vig_2026_mclp': None, 'proy_2027_mclp': 900},
        {'ini_2026_mclp': 0, 'vig_2026_mclp': 10, 'proy_2027_mclp': 30},
    ]
    res = resumen_presupuestario(rows)
    assert res['totales_mclp']['proyecto_2027'] == 1130
    assert res['totales_mclp']['dif_vs_ini'] == 130
    assert res['totales_mclp']['dif_vs_vig'] == 70
    assert res['comparables']['inicial']['total_programas'] == 2
    assert res['comparables']['inicial']['proyecto_2027_mclp'] == 230
    assert res['cobertura']['sin_base_inicial'] == 1
    assert resumen_presupuestario(rows[1:2])['totales_mclp']['dif_vs_ini'] is None


def test_dataset_corrige_entradas_y_no_imputa_cero():
    data = json.loads((ROOT/'data/comparativa_programas_2026_2027.json').read_text(encoding='utf-8'))
    by_code = {r['codigo']: r for r in data}
    assert len(by_code) == 515
    assert by_code['05-02-01']['proy_2027_mclp'] == 57329286
    assert by_code['31-01-14']['proy_2027_mclp'] == 86382592
    missing = [p for p in data if p['ini_2026_mclp'] is None]
    assert len(missing) == 58
    assert all(p['dif_vs_ini_mclp'] is None and p['pct_vs_ini'] is None for p in missing)
    assert by_code['18-01-60']['ini_2026_mclp'] == 0
    assert by_code['18-01-60']['pct_vs_ini'] is None
    assert by_code['18-01-60']['dif_vs_ini_mclp'] is not None
    assert all(p['fuente_2027']['autoridad'] == 'primaria_dipres_contraloria' for p in data)


def test_api_nulls_cobertura_y_recorrido_sin_cifras_ficticias():
    from server import app
    client = TestClient(app)
    payload = client.get('/api/presupuesto2027?q=09-46-02').json()
    assert payload['total_programas'] == 1
    assert payload['programas'][0]['ini_2026_mclp'] is None
    assert payload['totales_mclp']['dif_vs_ini'] is None
    assert payload['cobertura']['sin_base_inicial'] == 1
    route = client.get('/api/recorrido/09-46-02')
    assert route.status_code == 200
    assert 'None%' not in route.text
    assert 'Sin base' in route.text


def test_articulado_no_presenta_datos_deuda_erroneos_como_hechos():
    data = json.loads((ROOT/'data/matriz_articulado_2026_2027.json').read_text(encoding='utf-8'))
    debt = next(r for r in data if r['id'] == 'art-03-deuda')
    assert debt['calculo']['base_2026_millones_usd'] == 17400
    assert debt['calculo']['propuesta_2027_millones_usd'] == 25000
    assert debt['calculo']['variacion_pct'] == pytest.approx(43.67816091954023)
    assert '51,5' not in json.dumps(data, ensure_ascii=False)
    assert all(r['fuente_2026']['ley'] == '21.796' and r['fuente_2027']['pagina'] for r in data)
    portal = next(r for r in data if r['id'] == 'art-41-plataforma')
    assert portal['clasificacion'] == 'continuidad'
    assert all(r['estado_verificacion'] != 'oficial_2027_verificado' for r in data)


def test_no_asigna_computadores_a_programas_solo_por_ministerio():
    from bajada_calle import calcular_bajada_calle
    assert calcular_bajada_calle({'partida': '09', 'nombre_programa': 'Gestión administrativa',
                                 'dif_vs_ini_mclp': -10000000}) is None


def test_candidato_es_idempotente_y_rechaza_montos_nuevos_no_revisados(monkeypatch):
    import csv
    monkeypatch.syspath_prepend(str(ROOT/'scripts'))
    from revisar_presupuesto import generar_candidato
    rows = json.loads((ROOT/'data/comparativa_programas_2026_2027.json').read_text(encoding='utf-8'))
    evidencia = json.loads((ROOT/'data/verificacion_presupuestos_20261006.json').read_text(encoding='utf-8'))
    with (ROOT.parent/'data/ley_inicial_vigente_programa_julio_2026.csv').open(encoding='utf-8-sig') as f:
        base = list(csv.DictReader(f, delimiter=';'))
    candidato = generar_candidato(rows, base, evidencia)
    assert generar_candidato(candidato, base, evidencia) == candidato
    assert candidato == rows
    cambiado = [dict(r) for r in rows]
    cambiado[0]['proy_2027_mclp'] += 1
    with pytest.raises(ValueError, match='no revisado'):
        generar_candidato(cambiado, base, evidencia)


def test_exportacion_presupuesto_y_recorridos_coincide_con_api():
    from server import app
    client = TestClient(app)
    api = client.get('/api/presupuesto2027').json()
    exported = json.loads((ROOT/'docs/data/presupuesto2027.json').read_text(encoding='utf-8'))
    assert exported == api
    route = client.get('/api/recorrido/09-46-02').json()
    static = json.loads((ROOT/'docs/data/recorridos.json').read_text(encoding='utf-8'))
    assert static['09-46-02'] == route


def test_exportacion_preserva_acentos_y_muestra_fuentes(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'scripts'))
    from exportar_estatico import leer_csv
    rows = list(leer_csv(ROOT/'data/programas_evaluados_dipres.csv'))
    assert any('Educación' in str(r) for r in rows)
    exported = json.loads((ROOT/'docs/data/programas.json').read_text(encoding='utf-8'))
    assert not any('EducaciÃ' in str(r) for r in exported)
    matriz = json.loads((ROOT/'docs/data/matriz_articulado_2026_2027.json').read_text(encoding='utf-8'))
    assert matriz == json.loads((ROOT/'data/matriz_articulado_2026_2027.json').read_text(encoding='utf-8'))


def test_duckdb_tabla_determinista_y_sin_imputacion_cero():
    import duckdb
    db_path = ROOT / 'data/presupuesto_compras_db.duckdb'
    assert db_path.is_file()
    con = duckdb.connect(str(db_path), read_only=True)
    count = con.execute("SELECT count(*) FROM programas_2026_2027").fetchone()[0]
    assert count == 515
    nulls = con.execute("SELECT count(*) FROM programas_2026_2027 WHERE ini_2026_mclp IS NULL").fetchone()[0]
    assert nulls == 58
    art_count = con.execute("SELECT count(*) FROM articulado_2026_2027").fetchone()[0]
    assert art_count == 9
    con.close()

