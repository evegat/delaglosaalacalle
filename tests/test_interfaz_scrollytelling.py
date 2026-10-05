import gzip
import re
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]


def test_relatos_son_pasos_semanticos_y_navegables():
    text=(ROOT/'src/interfaz.html').read_text(encoding='utf-8')
    assert len(re.findall(r'data-paso="\d"',text))==4
    assert 'IntersectionObserver' in text
    assert 'prefers-reduced-motion' in text
    assert 'href="#evidencia"' in text
    assert '<noscript>' in text


def test_sin_trackers_ni_recursos_externos():
    text=(ROOT/'src/interfaz.html').read_text(encoding='utf-8')
    assert not re.search(r'(?:src|href)=[\"\x27]https?://',text)
    assert '<svg' in text and 'viewBox=' in text
    assert len(gzip.compress(text.encode()))<50*1024


def test_formularios_y_resultados_accesibles():
    text=(ROOT/'src/interfaz.html').read_text(encoding='utf-8')
    for token in ('for="busqueda"','for="servicio"','aria-live="polite"',
                  ':focus-visible','minmax(0','overflow-wrap','textContent','No disponible'):
        assert token in text
    assert 'innerHTML' not in text
    assert 'for="pregunta"' in text and "if(!r.ok)" in text
    assert 'Sin confirmación de registro' in text


def test_api_filtro_servicio_y_equivalencias(tmp_path,monkeypatch):
    import importlib.util
    from fastapi.testclient import TestClient
    import duckdb
    monkeypatch.setenv('P149_DATA_DIR',str(tmp_path))
    monkeypatch.syspath_prepend(str(ROOT/'src'))
    monkeypatch.setenv('P149_SQLITE_PATH',str(tmp_path/'preguntas.sqlite'))
    con=duckdb.connect(str(tmp_path/'presupuesto_compras_db.duckdb'))
    con.execute('CREATE TABLE programas_evaluados_dipres(nombre_programa VARCHAR, ministerio VARCHAR,servicio VARCHAR,motivo_variacion_presupuestaria VARCHAR,variacion_presupuesto_2025_2026_pct DOUBLE)')
    con.execute("INSERT INTO programas_evaluados_dipres VALUES ('Educación básica','Ministerio','Servicio A','',NULL),('Becas','Ministerio','Servicio B','',NULL)")
    con.close()
    spec=importlib.util.spec_from_file_location('server_frontend',ROOT/'src/server.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with TestClient(module.app) as client:
        rows=client.get('/api/programas',params={'q':'educacion','servicio':'Servicio B'}).json()
        assert rows==[]
        assert client.get('/api/servicios').json()==['Servicio A','Servicio B']
        assert client.get('/api/comparacion').json()['estado']=='no_disponible'
        catalog=client.get('/api/equivalencias').json()
        assert catalog['grupos']==[] and catalog['estado']=='sin_referencias_verificadas'
