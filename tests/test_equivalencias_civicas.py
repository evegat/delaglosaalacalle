"""Costos sintéticos; nunca se incorporan al catálogo publicado."""
import sys
from pathlib import Path
from decimal import Decimal
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from equivalencias_civicas import resumir_catalogo, equivalencia


def obs(costo,**cambios):
    r=dict(servicio='Luminarias',monto=costo*2,cantidad=2,unidad='luminaria instalada',
        moneda='CLP',territorio='Comuna ejemplo',periodo='2025',fuente='documento-local',verificada=True)
    r.update(cambios);return r


def test_n_dispersion_unidad_y_territorio_siempre_explicitos():
    g=resumir_catalogo([obs(100),obs(200),obs(300)])['grupos'][0]
    assert g['n']==3 and g['p50']==200
    assert g['p25']==150 and g['p75']==250
    assert g['desviacion_estandar']==100
    assert g['unidad']=='luminaria instalada' and g['territorio']=='Comuna ejemplo'
    assert not g['representativa_nacional']


def test_muestra_unica_no_inventa_dispersion():
    g=resumir_catalogo([obs(100)])['grupos'][0]
    assert g['n']==1 and g['desviacion_estandar'] is None
    assert 'única' in g['limite']


def test_no_agrupa_unidades_territorios_o_periodos_distintos():
    rows=[obs(100),obs(200,territorio='Otra comuna'),obs(300,unidad='luminaria sin instalación'),obs(100,periodo='2026')]
    assert len(resumir_catalogo(rows)['grupos'])==4


@pytest.mark.parametrize('cambios',[{'cantidad':0},{'cantidad':None},{'territorio':''},{'fuente':''},{'verificada':False}])
def test_referencias_incompletas_o_no_verificadas_se_excluyen(cambios):
    r=resumir_catalogo([obs(100,**cambios)])
    assert r['grupos']==[] and len(r['excluidas'])==1


def test_equivalencia_con_rango_y_limite_contable():
    g=resumir_catalogo([obs(100),obs(200),obs(300)])['grupos'][0]
    e=equivalencia(1000,g,territorio='Comuna ejemplo')
    assert e['cantidad_central']==5
    assert e['cantidad_minima']==4
    assert e['cantidad_maxima']==Decimal('1000')/150
    assert e['n']==3 and 'no predice' in e['advertencia']


def test_no_extrapola_costo_comunal_a_chile():
    g=resumir_catalogo([obs(100)])['grupos'][0]
    with pytest.raises(ValueError,match='territorio'):equivalencia(1000,g,territorio='Chile')


def test_estimacion_legacy_sin_cantidad_no_es_costo_unitario_verificado():
    r=resumir_catalogo([dict(costo_unitario_estimado=130000,monto_clp=2892110000)])
    assert r['grupos']==[]


def test_copias_identicas_no_inflan_tamano_de_muestra():
    r=resumir_catalogo([obs(100),obs(100)])
    assert r['grupos'][0]['n']==1
    assert len(r['excluidas'])==1
