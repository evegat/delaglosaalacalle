import pytest
import re
from pathlib import Path
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def client(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "src"))
    from server import app
    return TestClient(app)

def test_api_filtro_capitulo(client):
    """Verifica que el filtrado por capítulo en /api/presupuesto2027 funcione correctamente."""
    # Partida 16 (Salud), Capítulo 02 (FONASA)
    resp = client.get("/api/presupuesto2027?partida=16&capitulo=02")
    assert resp.status_code == 200
    data = resp.json()
    assert "programas" in data
    assert len(data["programas"]) > 0
    for p in data["programas"]:
        assert str(p["partida"]).zfill(2) == "16"
        assert str(p["capitulo"]).zfill(2) == "02"

def test_api_comision_mixta(client):
    """Verifica que /api/comision-mixta retorne los hitos con todos sus campos obligatorios."""
    resp = client.get("/api/comision-mixta")
    assert resp.status_code == 200
    data = resp.json()
    assert "hitos" in data
    assert data["total"] >= 6
    campos_esperados = ["id", "fecha", "instancia", "partida", "orador", "bajada_calle", "video_url_timestamp", "acta_url"]
    for h in data["hitos"]:
        for campo in campos_esperados:
            assert campo in h and str(h[campo]).strip() != ""

def test_api_comision_mixta_filtro_partida(client):
    """Verifica que /api/comision-mixta filtre correctamente por cartera."""
    resp = client.get("/api/comision-mixta?partida=09")
    assert resp.status_code == 200
    data = resp.json()
    for h in data["hitos"]:
        assert str(h["partida"]).zfill(2) == "09"

def test_html_integridad_filtros_y_radar():
    """Verifica la presencia de los nuevos controles y el cumplimiento de seguridad en HTML."""
    html_dist = (ROOT / "dist/index.html").read_text(encoding="utf-8")
    assert 'id="selector-capitulo-2027"' in html_dist, "dist/index.html debe contener el selector de capítulos"
    assert 'id="vista-mixta"' in html_dist, "dist/index.html debe contener la vista del Radar Comisión Mixta"
    assert 'id="tab-mixta"' in html_dist, "dist/index.html debe contener el tab de Comisión Mixta"
    # Regla estricta de seguridad: CERO href="https://" directos en HTML
    assert not re.search(r'(?:src|href)=[\"\']https?://', html_dist), "HTML no debe contener enlaces externos directos"
