"""Estadísticas descriptivas por servicio, territorio, unidad, moneda y período."""
from decimal import Decimal
from statistics import stdev


def _positivo(valor):
    try: n=Decimal(str(valor))
    except Exception:raise ValueError('Valor o cantidad no disponible') from None
    if not n.is_finite() or n<=0:raise ValueError('Valor y cantidad deben ser positivos')
    return n


def _percentil(ordenados,q):
    posicion=(len(ordenados)-1)*q
    entero=int(posicion);fraccion=posicion-entero
    return ordenados[entero]+fraccion*(ordenados[min(entero+1,len(ordenados)-1)]-ordenados[entero])


def resumir_catalogo(observaciones):
    grupos={};excluidas=[]
    claves=('servicio','unidad','moneda','territorio','periodo')
    for index,obs in enumerate(observaciones):
        try:
            if obs.get('verificada') is not True or not obs.get('fuente'):
                raise ValueError('Fuente sin verificación documentada')
            if any(not str(obs.get(c) or '').strip() for c in claves):
                raise ValueError('Faltan servicio, unidad, moneda, territorio o período')
            precio=_positivo(obs.get('monto'))/_positivo(obs.get('cantidad'))
            key=tuple(str(obs[c]).strip() for c in claves)
            grupos.setdefault(key,[]).append((precio,str(obs['fuente'])))
        except ValueError as exc:excluidas.append({'fila':index+1,'motivo':str(exc)})
    salida=[]
    for key,items in sorted(grupos.items()):
        precios=sorted(p for p,_ in items);n=len(precios)
        salida.append(dict(zip(claves,key),n=n,p25=_percentil(precios,Decimal('.25')),
            p50=_percentil(precios,Decimal('.5')),p75=_percentil(precios,Decimal('.75')),
            minimo=precios[0],maximo=precios[-1],
            desviacion_estandar=stdev(precios) if n>1 else None,
            fuentes=sorted(set(f for _,f in items)),representativa_nacional=False,
            metodo='Percentiles por interpolación lineal; desviación estándar muestral',
            limite='Observación única; no permite estimar dispersión' if n==1 else
                'Muestra observacional sin diseño representativo; no extrapolar a promedio nacional'))
    return {'grupos':salida,'excluidas':excluidas}


def equivalencia(monto,estadistica,*,territorio):
    if territorio!=estadistica['territorio']:
        raise ValueError('El territorio solicitado no coincide con la muestra')
    monto=_positivo(monto)
    return dict(estadistica,cantidad_central=monto/estadistica['p50'],
                cantidad_minima=monto/estadistica['p75'],cantidad_maxima=monto/estadistica['p25'],
                advertencia='Equivalencia contable orientativa; no predice servicios entregados o perdidos')
