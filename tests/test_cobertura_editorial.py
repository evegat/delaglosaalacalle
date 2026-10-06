"""La documentación exportada describe el mismo universo que los datos."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('cantidad', [0, 2, 3])
def test_documentacion_sigue_cobertura_exportada(tmp_path, monkeypatch, cantidad):
    monkeypatch.syspath_prepend(str(ROOT / 'src'))
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    import exportar_estatico as exportador

    filas = json.loads((ROOT / 'data/comparativa_programas_2026_2027.json').read_text(encoding='utf-8'))[:cantidad]
    for i, fila in enumerate(filas):
        fila['partida'] = '01' if i < 2 else '02'
    datos = tmp_path / 'data'
    datos.mkdir()
    (datos / 'comparativa_programas_2026_2027.json').write_text(json.dumps(filas), encoding='utf-8')
    monkeypatch.setattr(exportador, 'DATA_DIR', datos)
    monkeypatch.setattr(exportador, 'DIST_DIR', tmp_path / 'dist')
    monkeypatch.setattr(exportador, 'DOCS_DIR', tmp_path / 'docs')
    exportador.exportar_todo()

    for carpeta in ['dist', 'docs']:
        destino = tmp_path / carpeta
        payload = json.loads((destino / 'data/presupuesto2027.json').read_text(encoding='utf-8'))
        cobertura = f"{payload['total_programas']} programas presupuestarios en {len({p['partida'] for p in payload['programas']})} partidas"
        assert cobertura in (destino / 'llms.txt').read_text(encoding='utf-8')
        spec = json.loads((destino / 'openapi.json').read_text(encoding='utf-8'))
        operacion = spec['paths']['/data/presupuesto2027.json']['get']
        assert cobertura in operacion['summary']
        assert cobertura in operacion['description']
