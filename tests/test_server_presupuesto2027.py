import pytest
from pathlib import Path
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def client(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "src"))
    from server import app
    return TestClient(app)

def test_api_presupuesto_2027_retorna_programas_y_totales(client):
    res = client.get("/api/presupuesto2027")
    assert res.status_code == 200
    data = res.json()
    assert data["total_programas"] >= 150
    assert "totales_mclp" in data
    assert data["totales_mclp"]["proyecto_2027"] > 0
    assert data["totales_mclp"]["inicial_2026"] > 0

def test_api_presupuesto_2027_filtro_partida(client):
    res = client.get("/api/presupuesto2027?partida=29")
    assert res.status_code == 200
    data = res.json()
    assert data["total_programas"] >= 10
    for p in data["programas"]:
        assert p["partida"] == "29"

def test_api_presupuesto_2027_orden_mayor_recorte(client):
    res = client.get("/api/presupuesto2027?orden=mayor_recorte")
    assert res.status_code == 200
    data = res.json()
    progs = data["programas"]
    assert progs[0]["dif_vs_ini_mclp"] <= progs[1]["dif_vs_ini_mclp"]

def test_api_articulado_retorna_matriz_comparativa(client):
    res = client.get("/api/articulado")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 9
    
    # Ley 21.796, artículo 3: principal US$17.400M; adicional US$600M separado.
    art_deuda = next((a for a in data if "art-03" in a.get("id", "") or "Artículo 3" in a.get("articulo", "")), None)
    assert art_deuda is not None
    assert "25.000" in art_deuda["norma_2027"]
    assert "17.400" in art_deuda["norma_2026"]
    assert art_deuda["categoria"] == "Cambio"

    # Validar que el Artículo 40 (Freno SLEP) está presente
    art_slep = next((a for a in data if "art-40" in a.get("id", "") or "Artículo 40" in a.get("articulo", "")), None)
    assert art_slep is not None
    assert "Litoral" in art_slep["norma_2027"]
    assert art_slep["fuente_2026"]["articulo"] == "41"

