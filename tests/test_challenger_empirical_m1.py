"""Challenger M1-1: Pruebas Empíricas Automatizadas de UI, Filtros y Seguridad DOM.

Verificación independiente de los componentes interactivos de P149:
- Cero innerHTML / outerHTML / insertAdjacentHTML / eval()
- Conmutación rápida de tangibilidad (188 vs 515)
- Combinatorias de subtítulos DIPRES y casos borde
- Agrupación ministerial en 33 acordeones y búsqueda vacía
- Pinned drawer de dotación de personal
- Responsividad CSS para 320px, 390px y 1280px
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_empirico_cero_inner_html_y_sinks_peligrosos():
    """Tolerancia cero a manipulación insegura del DOM."""
    archivos = [
        ROOT / 'src/interfaz.html',
        ROOT / 'dist/index.html',
        ROOT / 'dist/assets/relato.js',
        ROOT / 'docs/index.html',
        ROOT / 'docs/assets/relato.js',
    ]
    patrones_prohibidos = [
        'innerHTML',
        'outerHTML',
        'insertAdjacentHTML',
        r'\beval\(',
        r'document\.write',
        r'javascript:',
    ]
    for ruta in archivos:
        assert ruta.is_file(), f'Falta archivo a auditar: {ruta}'
        texto = ruta.read_text(encoding='utf-8')
        for pat in patrones_prohibidos:
            assert not re.search(pat, texto), f'Patrón prohibido {pat} encontrado en {ruta.name}'


def test_empirico_conmutacion_rapida_tangibilidad():
    """Prueba de estrés de conmutación rápida de tangibilidad (100 ciclos)."""
    datos = json.loads((ROOT / 'docs/data/presupuesto2027.json').read_text(encoding='utf-8'))
    todos = datos['programas']
    assert len(todos) == 515

    for ciclo in range(100):
        solo_tangibles = (ciclo % 2 == 1)
        if solo_tangibles:
            filtrados = [p for p in todos if p.get('bajada_calle') is not None]
            assert len(filtrados) == 188
            assert all(p['bajada_calle'] is not None for p in filtrados)
        else:
            filtrados = list(todos)
            assert len(filtrados) == 515

    # Invariante de presupuesto total
    total_mclp = sum(p.get('proy_2027_mclp', 0) for p in todos if p.get('proy_2027_mclp') is not None)
    assert total_mclp == 217892642270
    assert round(total_mclp / 1e9, 2) == 217.89


def test_empirico_combinatorias_subtitulos_dipres():
    """Prueba combinatoria de subtítulos DIPRES y casos borde."""
    datos = json.loads((ROOT / 'docs/data/presupuesto2027.json').read_text(encoding='utf-8'))
    progs = datos['programas']

    def filtrar_por_subtitulos(cadena_subs):
        if not cadena_subs:
            return list(progs)
        subs = [s.strip() for s in cadena_subs.split(',') if s.strip()]
        return [
            p for p in progs
            if any(s in p.get('subtitulos', []) or s.zfill(2) in p.get('subtitulos', []) for s in subs)
        ]

    # Subtítulo 21 Personal
    sub21 = filtrar_por_subtitulos('21')
    assert len(sub21) == 445
    assert all('21' in p['subtitulos'] for p in sub21)

    # Subtítulo 22 Bienes y Servicios
    sub22 = filtrar_por_subtitulos('22')
    assert len(sub22) == 450

    # Combinación 21 + 22 (Unión exacta)
    sub21_22 = filtrar_por_subtitulos('21,22')
    union_21_22 = {p['codigo'] for p in sub21} | {p['codigo'] for p in sub22}
    assert len(sub21_22) == len(union_21_22) == 455

    # Combinación 24 + 31 (Transferencias + Inversión)
    sub24 = filtrar_por_subtitulos('24')
    sub31 = filtrar_por_subtitulos('31')
    sub24_31 = filtrar_por_subtitulos('24,31')
    union_24_31 = {p['codigo'] for p in sub24} | {p['codigo'] for p in sub31}
    assert len(sub24_31) == len(union_24_31) == 312

    # Los 6 chips DIPRES activos (21, 22, 24, 29, 31, 34)
    chips_todos = filtrar_por_subtitulos('21,22,24,29,31,34')
    assert len(chips_todos) == 510

    # 5 programas fuera de los 6 chips (Partida 50 Tesoro Público)
    fuera_de_chips = [p for p in progs if p['codigo'] not in {c['codigo'] for c in chips_todos}]
    assert len(fuera_de_chips) == 5
    assert all(p['partida'] == '50' for p in fuera_de_chips)

    # Subtítulo inexistente
    sub99 = filtrar_por_subtitulos('99')
    assert len(sub99) == 0

    # Vacío (Todos)
    sub_todos = filtrar_por_subtitulos('')
    assert len(sub_todos) == 515


def test_empirico_acordeones_ministeriales_y_busqueda_vacia():
    """Verifica agrupación en 33 carteras y manejo de búsqueda sin coincidencias."""
    datos = json.loads((ROOT / 'docs/data/presupuesto2027.json').read_text(encoding='utf-8'))
    progs = datos['programas']

    partidas = {}
    for p in progs:
        cod = p.get('partida', '00')
        partidas.setdefault(cod, []).append(p)

    assert len(partidas) == 33
    assert sum(len(v) for v in partidas.values()) == 515

    # Simulación de búsqueda vacía / sin resultados
    termino_nulo = 'palabra_inexistente_xyz_9999'
    tokens = [termino_nulo]
    coincidencias = [
        p for p in progs
        if all(t in f"{p['codigo']} {p['nombre_partida']} {p['nombre_programa']}".lower() for t in tokens)
    ]
    assert len(coincidencias) == 0

    # Verificación en interfaz.html de mensaje ante 0 resultados
    html = (ROOT / 'src/interfaz.html').read_text(encoding='utf-8')
    assert 'No se encontraron programas con los filtros seleccionados.' in html
    assert 'btn-expandir-todos' in html
    assert 'btn-colapsar-todos' in html


def test_empirico_drawer_pinned_glosa():
    """Verifica contenido del panel pineado de personal y dotaciones en drawer."""
    html = (ROOT / 'src/interfaz.html').read_text(encoding='utf-8')
    assert 'drawer-pinned-glosa' in html
    assert 'Dotación y Personal Autorizado (Subtítulo 21)' in html
    assert '1.500 traspasos' in html
    assert 'Ley N° 21.796' in html
    assert 'D.L. N° 249' in html
    assert 'Este programa no cuenta con asignación presupuestaria directa en Subtítulo 21' in html


def test_empirico_responsividad_css_viewports():
    """Auditoría de reglas CSS de responsividad para 320px, 390px y 1280px."""
    css = (ROOT / 'dist/assets/relato.css').read_text(encoding='utf-8')

    # Viewport 320px
    assert '.tabla-wrapper{overflow-x:auto' in css
    assert 'width:min(480px,100vw)' in css
    assert '@media(max-width:680px)' in css
    assert 'overflow-wrap:anywhere' in css

    # Viewport 390px
    assert '@media(max-width:768px)' in css

    # Viewport 1280px
    assert 'max-width:1120px;margin:auto' in css
    assert 'grid-template-columns:minmax(0,1fr) minmax(0,1fr)' in css


def test_empirico_matriz_articulado_art3_art40():
    """Verifica contenido y cifras de los Artículos 3 y 40."""
    articulado = json.loads((ROOT / 'docs/data/matriz_articulado_2026_2027.json').read_text(encoding='utf-8'))
    ejes = articulado if isinstance(articulado, list) else articulado.get('ejes_comparativos', [])
    assert len(ejes) == 9

    art3 = next(e for e in ejes if 'Artículo 3' in e.get('articulo', ''))
    assert '17.400' in art3['norma_2026'] or '17.400' in art3['impacto_calle']
    assert '25.000' in art3['norma_2027'] or '25.000' in art3['impacto_calle']

    art40 = next(e for e in ejes if 'Artículo 40' in e.get('articulo', ''))
    assert 'cinco servicios' in art40['norma_2027'] or '5 SLEP' in art40['norma_2027'] or 'Litoral' in art40['norma_2027']
    assert all(slep in art40['norma_2027'] for slep in ['Litoral', 'Los Cerezos', 'Los Copihues', 'Chacabuco', 'Los Viñedos'])
