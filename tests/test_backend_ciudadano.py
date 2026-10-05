import importlib.util
import shutil
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def api(tmp_path, monkeypatch):
    app_dir = tmp_path / "app"
    (app_dir / "src").mkdir(parents=True)
    (app_dir / "data").mkdir()
    shutil.copyfile(ROOT / "src/server.py", app_dir / "src/server.py")
    for name in ("busqueda_programas.py",):
        if (ROOT / "src" / name).exists():
            shutil.copyfile(ROOT / "src" / name, app_dir / "src" / name)
    monkeypatch.syspath_prepend(str(app_dir / "src"))
    monkeypatch.setenv("P149_DATA_DIR", str(app_dir / "data"))
    monkeypatch.setenv("P149_RATE_LIMIT", "3")
    monkeypatch.setenv("P149_RATE_WINDOW_SECONDS", "600")
    con = duckdb.connect(str(app_dir / "data/presupuesto_compras_db.duckdb"))
    con.execute("""CREATE TABLE programas_evaluados_dipres (
      id_bips INTEGER, ministerio VARCHAR, servicio VARCHAR, nombre_programa VARCHAR,
      motivo_variacion_presupuestaria VARCHAR, variacion_presupuesto_2025_2026_pct DOUBLE)""")
    con.executemany("INSERT INTO programas_evaluados_dipres VALUES (?,?,?,?,?,?)", [
        (1, "Educación", "Junaeb", "Becas de educación superior", "Reasignación de recursos", -12.0),
        (2, "Salud", "Atención primaria", "Salud de la infancia", "Continuidad del servicio", 3.0),
    ])
    con.close()
    spec = importlib.util.spec_from_file_location("p149_server_test", app_dir / "src/server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with TestClient(module.app) as client:
        yield client, module


def test_accent_and_compound_query(api):
    client, _ = api
    plain = client.get("/api/programas", params={"q": "becas educacion"})
    accented = client.get("/api/programas", params={"q": "BECAS EDUCACIÓN"})
    assert plain.status_code == accented.status_code == 200
    assert [p["id_bips"] for p in plain.json()] == [1]
    assert plain.json() == accented.json()
    assert client.get("/api/programas", params={"q": "becas salud"}).json() == []


@pytest.mark.parametrize("text", ["    ", "?????", "<script>alert(1)</script>", "&lt;img src=x&gt;", "becas\u202eeducacion"])
def test_reject_invalid_question(api, text):
    client, _ = api
    assert client.post("/api/preguntas", json={"pregunta": text}).status_code == 422


def test_normalization_and_honest_response(api):
    client, _ = api
    response = client.post("/api/preguntas", json={"pregunta": "  Becas\n de educacio\u0301n  "})
    assert response.status_code == 200
    result = response.json()
    assert result["ok"] and result["id"]
    assert result["tipo_coincidencia"] == "textual_orientativa"
    assert result["periodo_datos"] == "2025–2026"
    assert result["match_encontrado"]
    assert not result["respuesta_personalizada"]


def test_connection_pragmas_and_timezone(api):
    client, module = api
    with module.get_db_connection() as con:
        assert con.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert con.execute("PRAGMA synchronous").fetchone()[0] == 1
        assert con.execute("PRAGMA busy_timeout").fetchone()[0] >= 5000
    countdown = client.get("/api/countdown").json()
    assert countdown["objetivo_iso"].endswith("-03:00")
    assert "oficial" not in countdown["mensaje"].lower()


def test_atomic_rate_limit_shared_between_connections(api):
    client, module = api
    def send(_):
        return client.post("/api/preguntas", json={"pregunta": "Consulta sobre becas educación"})
    with ThreadPoolExecutor(max_workers=6) as executor:
        responses = list(executor.map(send, range(9)))
    assert [r.status_code for r in responses].count(200) == 3
    assert [r.status_code for r in responses].count(429) == 6
    assert all("Retry-After" in r.headers for r in responses if r.status_code == 429)
    con = sqlite3.connect(module.SQLITE_PATH)
    assert con.execute("SELECT COUNT(*) FROM preguntas_ciudadanas").fetchone()[0] == 3
    con.close()


def test_public_questions_do_not_expose_text_or_contact(api):
    client, _ = api
    assert client.post("/api/preguntas", json={"pregunta": "Consulta sobre becas educación", "comuna": "Cabildo"}).status_code == 200
    public = client.get("/api/preguntas").json()
    assert isinstance(public, list)
    assert len(public) == 1
    assert "pregunta" not in public[0] and "comuna" not in public[0] and "contacto" not in public[0]
    assert client.get("/api/preguntas", params={"limit": -1}).status_code == 422


def test_unavailable_analysis_does_not_lose_question(api):
    client, module = api
    module.DB_PATH = module.DATA_DIR / "missing.duckdb"
    assert client.get("/api/programas").status_code == 503
    response = client.post("/api/preguntas", json={"pregunta": "Consulta sobre becas educación"})
    assert response.status_code == 200
    assert response.json()["busqueda_disponible"] is False
    assert response.json()["ok"] is True
