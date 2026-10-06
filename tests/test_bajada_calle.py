"""Tests unitarios y de integración para el motor de Bajada a la Calle (P149)."""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "src"))
    from server import app
    return TestClient(app)


def test_bajada_calle_becas_tic(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "src"))
    from bajada_calle import estimar_bajada_calle
    prog = {
        "codigo": "09-09-03",
        "nombre_programa": "BECAS Y ASISTENCIALIDAD ESTUDIANTIL",
        "nombre_partida": "Educación",
        "dif_vs_ini_mclp": -31051,
        "dif_vs_vig_mclp": -25000
    }
    bajada = estimar_bajada_calle(prog)
    assert bajada is not None
    assert bajada["signo"] == "-"
    assert bajada["icono"] == "💻"
    assert "notebooks" in bajada["unidad"]
    assert bajada["costo_unitario_clp"] == 330000
    assert bajada["cantidad"] > 90000
    assert "menos" in bajada["impacto_texto"]
    assert "JUNAEB" in bajada["organismo"]


def test_bajada_calle_quiero_mi_barrio(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "src"))
    from bajada_calle import estimar_bajada_calle
    prog = {
        "codigo": "18-01-04",
        "nombre_programa": "Recuperación de Barrios",
        "nombre_partida": "Vivienda y Urbanismo",
        "dif_vs_ini_mclp": -30171,
        "dif_vs_vig_mclp": 1500
    }
    bajada = estimar_bajada_calle(prog)
    assert bajada is not None
    assert bajada["signo"] == "-"
    assert bajada["icono"] == "🏘️"
    assert "barrio" in bajada["unidad"]
    assert bajada["costo_unitario_clp"] == 350000000
    assert bajada["cantidad"] == 86
    assert "plazas" in bajada["unidad"]


def test_bajada_calle_api_presupuesto2027(client):
    res = client.get("/api/presupuesto2027?q=Barrios")
    assert res.status_code == 200
    data = res.json()
    assert len(data["programas"]) >= 1
    prog = data["programas"][0]
    assert "bajada_calle" in prog
    assert prog["bajada_calle"] is not None
    assert prog["bajada_calle"]["icono"] == "🏘️"
