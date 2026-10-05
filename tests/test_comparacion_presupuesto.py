"""Fixtures sintéticas: no representan inflación ni presupuestos observados."""
import sys
from pathlib import Path
from decimal import Decimal

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from comparacion_presupuesto import comparar_presupuestos, IndiceIPC


def fila(monto, nombre='Programa', **cambios):
    return dict(partida='05', capitulo='01', programa='02', subtitulo='24',
                item='01', asignacion='001', denominacion=nombre, monto=monto,
                moneda='CLP', unidad='pesos', **cambios)


def test_cambio_de_denominacion_no_rompe_identidad():
    r = comparar_presupuestos([fila(100, 'Nombre previo')], [fila(110, 'Nuevo nombre')])[0]
    assert r['monto_2025'] == 100 and r['monto_2026'] == 110
    assert r['variacion_nominal_pct'] == Decimal('10')
    assert r['denominacion_2025'] != r['denominacion_2026']
    assert r['variacion_real_pct'] is None


@pytest.mark.parametrize('campo,valor', [('partida','06'), ('capitulo','03'),
    ('programa','04'), ('subtitulo','33'), ('item','02'), ('asignacion','002')])
def test_cada_segmento_forma_parte_de_la_clave(campo, valor):
    nuevo = fila(200); nuevo[campo] = valor
    r = comparar_presupuestos([fila(100)], [nuevo])
    assert len(r) == 2
    assert all(x['variacion_nominal_pct'] is None for x in r)


def test_discontinuado_no_es_recorte_demostrado():
    r = comparar_presupuestos([fila(100)], [])[0]
    assert r['monto_2026'] is None
    assert r['estado'] == 'no_reportado_2026'
    assert r['variacion_real_pct'] is None


def test_programa_nuevo_no_es_aumento_desde_cero():
    r = comparar_presupuestos([], [fila(100)])[0]
    assert r['monto_2025'] is None
    assert r['estado'] == 'no_reportado_2025'
    assert r['variacion_nominal_pct'] is None


@pytest.mark.parametrize('monto', [None, '', 'N/D'])
def test_monto_no_reportado_permanece_null(monto):
    r = comparar_presupuestos([fila(monto)], [fila(100)])[0]
    assert r['monto_2025'] is None
    assert r['variacion_real_pct'] is None


def test_cero_explicito_y_base_positiva():
    r = comparar_presupuestos([fila(100)], [fila(0)])[0]
    assert r['monto_2026'] == 0
    assert r['variacion_nominal_pct'] == -100
    assert r['variacion_real_pct'] is None


def test_porcentaje_real_por_cociente_de_indices():
    ipc = IndiceIPC(Decimal('100'), Decimal('105'),
        'https://www.ine.gob.cl/estadisticas/economia/indices-de-precio-e-inflacion',
        '2025', '2026', verificado=True)
    r = comparar_presupuestos([fila(100)], [fila(110)], ipc=ipc)[0]
    assert abs(r['variacion_real_pct'] - Decimal('4.7619047619047619')) < Decimal('1e-12')
    assert r['fuente_ipc'] == ipc.fuente


def test_ipc_no_verificado_o_periodo_incorrecto_no_calcula():
    for verificado, periodo in [(False,'2026'), (True,'2027')]:
        ipc=IndiceIPC(100,105,'https://www.ine.gob.cl/ipc', '2025',periodo,verificado)
        assert comparar_presupuestos([fila(100)],[fila(110)],ipc=ipc)[0]['variacion_real_pct'] is None


def test_duplicados_discordantes_no_se_suman():
    r = comparar_presupuestos([fila(100), fila(200)], [fila(250)])[0]
    assert r['estado'] == 'ambiguo'
    assert r['monto_2025'] is None and r['variacion_nominal_pct'] is None


def test_copias_identicas_no_duplican_presupuesto():
    assert comparar_presupuestos([fila(100), fila(100)], [fila(110)])[0]['monto_2025'] == 100


@pytest.mark.parametrize('campo', ['item','asignacion'])
def test_codigo_incompleto_no_se_rellena_con_ceros(campo):
    f=fila(100);del f[campo]
    with pytest.raises(ValueError, match='Código'):
        comparar_presupuestos([f], [])


def test_unidades_incompatibles_no_se_comparan():
    f=fila(100);f['unidad']='miles de pesos'
    r=comparar_presupuestos([fila(100)],[f])[0]
    assert r['estado']=='unidad_incompatible' and r['variacion_nominal_pct'] is None


@pytest.mark.parametrize('monto', ['NaN','Infinity',-1])
def test_montos_invalidos_no_entran(monto):
    with pytest.raises(ValueError):comparar_presupuestos([fila(monto)],[])


def test_codigos_numericos_integrales_de_excel():
    f=fila(100);f['partida']=5.0
    assert comparar_presupuestos([f],[fila(110)])[0]['variacion_nominal_pct']==10
