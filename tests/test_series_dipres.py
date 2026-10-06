"""Series DIPRES por programa y subtítulo; comparación multiserie (FEAT-P149-COMPARADOR-MULTISERIE).

Fixtures sintéticas salvo el test marcado con el original DIPRES local.
"""
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from series_dipres import (  # noqa: E402
    FactorIndexacion,
    comparar_series,
    leer_csv_datos_abiertos,
    totales_programa,
)

ENCABEZADO = ('Año;Mes;Moneda;Partida;Nombre Partida;Capítulo;Nombre Capítulo;Programa;Nombre Programa;'
              'Subtítulo;Nombre Subtítulo;Item;Nombre Item;Asignación;Nombre Asignación;'
              'Monto Ley Inicial;Monto Ley Vigente a Julio')


def _csv(tmp_path, *filas):
    path = tmp_path / 'ley_inicial_vigente_programa_julio_2026.csv'
    path.write_text('\n'.join((ENCABEZADO,) + filas) + '\n', encoding='utf-8-sig')
    return path


def test_lee_solo_subtitulos_sin_doble_conteo_y_genera_dos_series(tmp_path):
    path = _csv(tmp_path,
        '2026;Julio;Pesos;9;MINEDUC;9;JUNAEB;2;Alimentación Escolar;22;BIENES Y SERVICIOS;;;;;1.000;900',
        '2026;Julio;Pesos;9;MINEDUC;9;JUNAEB;2;Alimentación Escolar;22;BIENES Y SERVICIOS;1;Alimentos;;;600;500',
        '2026;Julio;Pesos;9;MINEDUC;9;JUNAEB;2;Alimentación Escolar;22;BIENES Y SERVICIOS;1;Alimentos;001;Raciones;600;500',
        '2026;Julio;Pesos;9;MINEDUC;9;JUNAEB;2;Alimentación Escolar;9;APORTE FISCAL;;;;;1.000;900')
    filas = leer_csv_datos_abiertos(path)
    gasto = [f for f in filas if f['tipo'] == 'gasto']
    assert {f['serie'] for f in gasto} == {'inicial_2026', 'vigente_2026'}
    assert len(gasto) == 2
    ini = next(f for f in gasto if f['serie'] == 'inicial_2026')
    assert ini['monto'] == Decimal('1000')
    assert (ini['partida'], ini['capitulo'], ini['programa'], ini['subtitulo']) == ('09', '09', '02', '22')
    assert ini['nombre_programa'] == 'Alimentación Escolar'
    assert ini['moneda'] == 'CLP' and ini['unidad'] == 'miles'
    assert {f['tipo'] for f in filas} == {'gasto', 'ingreso'}


def test_monedas_separadas_y_monto_vacio_es_null(tmp_path):
    path = _csv(tmp_path,
        '2026;Julio;Dolares;6;RREE;1;SEC;1;Servicio Exterior;22;BYS;;;;;660;',
        '2026;Julio;Pesos;6;RREE;1;SEC;1;Servicio Exterior;22;BYS;;;;;100;100')
    filas = leer_csv_datos_abiertos(path)
    vig_usd = next(f for f in filas if f['moneda'] == 'USD' and f['serie'] == 'vigente_2026')
    assert vig_usd['monto'] is None
    assert {f['moneda'] for f in filas} == {'USD', 'CLP'}


def test_monto_con_formato_ambiguo_se_rechaza(tmp_path):
    path = _csv(tmp_path, '2026;Julio;Pesos;9;M;9;J;2;P;22;B;;;;;1,5;1')
    with pytest.raises(ValueError, match='Monto'):
        leer_csv_datos_abiertos(path)


def test_monto_negativo_publicado_por_dipres_se_conserva(tmp_path):
    # Regresión con original 2026: DIPRES publica ajustes negativos (p. ej. -2.039.165).
    path = _csv(tmp_path, '2026;Julio;Pesos;9;M;9;J;2;P;22;B;;;;;100;-2.039.165')
    vig = next(f for f in leer_csv_datos_abiertos(path) if f['serie'] == 'vigente_2026')
    assert vig['monto'] == Decimal('-2039165')


def test_totales_programa_suman_solo_gasto_por_moneda():
    filas = [
        dict(serie='inicial_2026', moneda='CLP', unidad='miles', tipo='gasto', partida='09', capitulo='09',
             programa='02', subtitulo=s, nombre_programa='PAE', monto=Decimal(m))
        for s, m in (('21', '10'), ('22', '90'))
    ] + [dict(serie='inicial_2026', moneda='CLP', unidad='miles', tipo='ingreso', partida='09', capitulo='09',
              programa='02', subtitulo='09', nombre_programa='PAE', monto=Decimal('100'))]
    tot = totales_programa(filas)
    assert len(tot) == 1 and tot[0]['monto'] == Decimal('100') and tot[0]['subtitulo'] == 'TOTAL_GASTO'


def _fila(serie, monto, programa='02', moneda='CLP'):
    return dict(serie=serie, moneda=moneda, unidad='miles', tipo='gasto', partida='09', capitulo='09',
                programa=programa, subtitulo='22', nombre_programa='PAE', monto=monto)


PARES = [('proyecto_2027', 'inicial_2026'), ('proyecto_2027', 'vigente_2026'), ('inicial_2026', 'inicial_2025')]


def test_compara_cuatro_series_y_marca_serie_ausente():
    filas = [_fila('inicial_2026', Decimal('100')), _fila('vigente_2026', Decimal('80')),
             _fila('inicial_2025', Decimal('90'))]
    [r] = comparar_series(filas, PARES)
    assert r['montos'] == {'proyecto_2027': None, 'inicial_2026': Decimal('100'),
                           'vigente_2026': Decimal('80'), 'inicial_2025': Decimal('90')}
    d = {(x['a'], x['b']): x for x in r['diferencias']}
    assert d[('proyecto_2027', 'inicial_2026')]['estado'] == 'no_reportado_proyecto_2027'
    assert d[('proyecto_2027', 'inicial_2026')]['diferencia_nominal'] is None
    x = d[('inicial_2026', 'inicial_2025')]
    assert x['estado'] == 'comparable' and x['diferencia_nominal'] == Decimal('10')
    assert x['diferencia_real'] is None and x['motivo_real']


def test_cero_explicito_no_es_ausencia():
    filas = [_fila('proyecto_2027', Decimal('0')), _fila('inicial_2026', Decimal('100'))]
    [r] = comparar_series(filas, PARES[:1])
    x = r['diferencias'][0]
    assert x['estado'] == 'cero_explicito_proyecto_2027'
    assert x['diferencia_nominal'] == Decimal('-100') and x['variacion_nominal_pct'] == Decimal('-100')


def test_monedas_distintas_no_se_cruzan():
    filas = [_fila('proyecto_2027', Decimal('5'), moneda='USD'), _fila('inicial_2026', Decimal('100'))]
    resultado = comparar_series(filas, PARES[:1])
    assert len(resultado) == 2
    assert all(r['diferencias'][0]['diferencia_nominal'] is None for r in resultado)


def test_serie_duplicada_con_montos_distintos_es_ambigua():
    filas = [_fila('inicial_2026', Decimal('100')), _fila('inicial_2026', Decimal('101')),
             _fila('inicial_2025', Decimal('90'))]
    [r] = comparar_series(filas, PARES[2:])
    assert r['diferencias'][0]['estado'] == 'ambiguo' and r['montos']['inicial_2026'] is None


def test_real_solo_con_factor_verificado_de_fuente_oficial():
    filas = [_fila('inicial_2026', Decimal('110')), _fila('inicial_2025', Decimal('100'))]
    ine = FactorIndexacion(serie='inicial_2025', base='pesos_2026', factor=Decimal('1.05'),
                           fuente='https://www.ine.gob.cl/estadisticas/economia/indices-de-precio-e-inflacion',
                           periodo='promedio 2025 a promedio 2026', verificado=True)
    ident = FactorIndexacion.identidad('inicial_2026', 'pesos_2026')
    [r] = comparar_series(filas, PARES[2:], factores=[ine, ident])
    x = r['diferencias'][0]
    assert x['diferencia_real'] == Decimal('110') - Decimal('105.00')
    assert x['base_real'] == 'pesos_2026' and 'ine.gob.cl' in x['fuentes_real'][0]

    no_verificado = FactorIndexacion(serie='inicial_2025', base='pesos_2026', factor=Decimal('1.05'),
                                     fuente='https://www.ine.gob.cl/x', periodo='p', verificado=False)
    blog = FactorIndexacion(serie='inicial_2025', base='pesos_2026', factor=Decimal('1.05'),
                            fuente='https://blog.example.com/ipc', periodo='p', verificado=True)
    for malo in (no_verificado, blog):
        [r] = comparar_series(filas, PARES[2:], factores=[malo, ident])
        assert r['diferencias'][0]['diferencia_real'] is None


def test_real_exige_misma_base_en_ambas_series():
    filas = [_fila('inicial_2026', Decimal('110')), _fila('inicial_2025', Decimal('100'))]
    a = FactorIndexacion(serie='inicial_2025', base='pesos_2026', factor=Decimal('1.05'),
                         fuente='https://www.ine.gob.cl/x', periodo='p', verificado=True)
    b = FactorIndexacion.identidad('inicial_2026', 'pesos_2027')
    [r] = comparar_series(filas, PARES[2:], factores=[a, b])
    assert r['diferencias'][0]['diferencia_real'] is None


ORIGINAL = Path(__file__).resolve().parents[2] / 'data' / 'ley_inicial_vigente_programa_julio_2026.csv'


@pytest.mark.skipif(not ORIGINAL.exists(), reason='Original DIPRES fuera del repositorio')
def test_original_dipres_educacion_cuadra_con_total_de_partida_publicado():
    # Total de gastos Partida 09 publicado por DIPRES (Excel resumen de partida,
    # articles-397474_doc_xls.xls, Ley 2026, "Miles de $"): 22.378.057.695.
    filas = [f for f in leer_csv_datos_abiertos(ORIGINAL)
             if f['partida'] == '09' and f['moneda'] == 'CLP' and f['serie'] == 'inicial_2026']
    assert sum(t['monto'] for t in totales_programa(filas)) == Decimal('22378057695')
