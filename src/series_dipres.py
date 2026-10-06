"""Series presupuestarias DIPRES por programa × subtítulo y comparación multiserie.

Fuente principal: datos abiertos DIPRES `ley_inicial_vigente_programa_<mes>_<año>.csv`
(separador `;`, punto de miles, filas jerárquicas subtítulo → ítem → asignación).
Solo se leen filas de subtítulo (ítem vacío): el detalle ya está contenido en ellas
y sumarlo duplicaría montos. Unidad CLP verificada el 05-10-2026: la suma de gastos
de la Partida 09 coincide con el total en «Miles de $» del Excel de partida DIPRES.

No hay IPC ni reajuste por defecto. Un monto real solo existe cuando ambas series
tienen factor hacia la misma base, de fuente oficial y marcado como verificado.
"""
import csv
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

MONEDAS = {'pesos': ('CLP', 'miles'), 'dolares': ('USD', 'miles_no_verificada')}
ANCHOS = {'partida': 2, 'capitulo': 2, 'programa': 2, 'subtitulo': 2}
COLUMNAS = {'partida': 'Partida', 'capitulo': 'Capítulo', 'programa': 'Programa', 'subtitulo': 'Subtítulo'}
HOSTS_OFICIALES = ('ine.gob.cl', 'ine.cl', 'dipres.gob.cl', 'dipres.cl')
SUBTITULO_GASTO_MIN = 21


def _monto(valor):
    texto = (valor or '').strip()
    if not texto:
        return None
    if not re.fullmatch(r'-?(?:\d{1,3}(?:\.\d{3})*|\d+)', texto):
        raise ValueError(f'Monto con formato no reconocido: {texto!r}')
    return Decimal(texto.replace('.', ''))


def _codigo(valor, campo):
    texto = (valor or '').strip()
    if not texto.isascii() or not texto.isdigit() or len(texto) > ANCHOS[campo]:
        raise ValueError(f'Código {campo} ausente o inválido: {texto!r}')
    return texto.zfill(ANCHOS[campo])


def leer_csv_datos_abiertos(path):
    """Devuelve una fila por serie (inicial_<año>, vigente_<año>) y subtítulo."""
    path = Path(path)
    with path.open(encoding='utf-8-sig', newline='') as f:
        lector = csv.DictReader(f, delimiter=';')
        campos = lector.fieldnames or []
        col_vigente = next((c for c in campos if c.startswith('Monto Ley Vigente')), None)
        requeridas = ['Año', 'Moneda', 'Item', 'Monto Ley Inicial', *COLUMNAS.values()]
        if col_vigente is None or any(c not in campos for c in requeridas):
            raise ValueError('CSV sin columnas DIPRES esperadas')
        salida = []
        for numero, fila in enumerate(lector, 2):
            if not (fila['Subtítulo'] or '').strip() or (fila['Item'] or '').strip():
                continue
            moneda = MONEDAS.get(fila['Moneda'].strip().casefold())
            if moneda is None:
                raise ValueError(f'Moneda no reconocida en fila {numero}: {fila["Moneda"]!r}')
            ano = int(fila['Año'])
            codigos = {k: _codigo(fila[c], k) for k, c in COLUMNAS.items()}
            base = dict(codigos, moneda=moneda[0], unidad=moneda[1],
                        tipo='gasto' if int(codigos['subtitulo']) >= SUBTITULO_GASTO_MIN else 'ingreso',
                        nombre_partida=fila.get('Nombre Partida', ''), nombre_capitulo=fila.get('Nombre Capítulo', ''),
                        nombre_programa=fila.get('Nombre Programa', ''), nombre_subtitulo=fila.get('Nombre Subtítulo', ''),
                        fuente=path.name, fila=numero, corte=fila.get('Mes', ''))
            salida.append(dict(base, serie=f'inicial_{ano}', monto=_monto(fila['Monto Ley Inicial'])))
            salida.append(dict(base, serie=f'vigente_{ano}', monto=_monto(fila[col_vigente])))
    return salida


def totales_programa(filas):
    """Total de gasto por serie, moneda y programa; NULL si algún subtítulo es NULL."""
    grupos = {}
    for f in filas:
        if f['tipo'] != 'gasto':
            continue
        clave = (f['serie'], f['moneda'], f['unidad'], f['partida'], f['capitulo'], f['programa'])
        g = grupos.setdefault(clave, {'monto': Decimal(0), 'nulo': False, 'nombre_programa': f.get('nombre_programa')})
        if f['monto'] is None:
            g['nulo'] = True
        else:
            g['monto'] += f['monto']
    return [dict(zip(('serie', 'moneda', 'unidad', 'partida', 'capitulo', 'programa'), k),
                 subtitulo='TOTAL_GASTO', tipo='gasto', nombre_programa=g['nombre_programa'],
                 monto=None if g['nulo'] else g['monto'])
            for k, g in sorted(grupos.items())]


@dataclass(frozen=True)
class FactorIndexacion:
    serie: str
    base: str
    factor: Decimal
    fuente: str
    periodo: str
    verificado: bool = False

    @classmethod
    def identidad(cls, serie, base):
        return cls(serie=serie, base=base, factor=Decimal(1), fuente='identidad', periodo=base, verificado=True)

    def valido(self):
        if self.fuente == 'identidad':
            return self.factor == 1
        host = urlparse(self.fuente).hostname or ''
        oficial = any(host == h or host.endswith('.' + h) for h in HOSTS_OFICIALES)
        return bool(self.verificado and oficial and self.factor and self.factor > 0)


def _pct(a, b):
    return (a / b - 1) * 100 if a is not None and b is not None and b > 0 else None


def comparar_series(filas, pares, factores=None):
    """Une series por moneda/unidad/programa/subtítulo y calcula diferencias por par (a − b)."""
    series = list(dict.fromkeys(s for par in pares for s in par))
    factores = {f.serie: f for f in (factores or []) if f.valido()}
    grupos = {}
    for f in filas:
        if f['serie'] not in series:
            continue
        clave = (f['moneda'], f['unidad'], f['partida'], f['capitulo'], f['programa'], f['subtitulo'])
        g = grupos.setdefault(clave, {'valores': {}, 'nombre_programa': f.get('nombre_programa')})
        g['valores'].setdefault(f['serie'], set()).add(f['monto'])
    salida = []
    for clave, g in sorted(grupos.items()):
        ambiguas = {s for s, v in g['valores'].items() if len(v) > 1}
        montos = {s: (next(iter(g['valores'][s])) if s in g['valores'] and s not in ambiguas else None)
                  for s in series}
        diferencias = []
        for a, b in pares:
            ma, mb = montos[a], montos[b]
            if a in ambiguas or b in ambiguas: estado = 'ambiguo'
            elif ma is None: estado = f'no_reportado_{a}'
            elif mb is None: estado = f'no_reportado_{b}'
            elif ma == 0 and mb == 0: estado = 'cero_explicito_ambos'
            elif ma == 0: estado = f'cero_explicito_{a}'
            elif mb == 0: estado = f'cero_explicito_{b}'
            else: estado = 'comparable'
            ok = estado != 'ambiguo' and ma is not None and mb is not None
            fa, fb = factores.get(a), factores.get(b)
            real = ok and fa is not None and fb is not None and fa.base == fb.base
            ra, rb = (ma * fa.factor, mb * fb.factor) if real else (None, None)
            diferencias.append({
                'a': a, 'b': b, 'estado': estado,
                'diferencia_nominal': ma - mb if ok else None,
                'variacion_nominal_pct': _pct(ma, mb) if ok else None,
                'diferencia_real': ra - rb if real else None,
                'variacion_real_pct': _pct(ra, rb) if real else None,
                'base_real': fa.base if real else None,
                'fuentes_real': [f.fuente for f in (fa, fb) if f.fuente != 'identidad'] if real else [],
                'motivo_real': None if real else
                    'Requiere ambos montos y factores verificados de fuente oficial hacia la misma base',
            })
        salida.append(dict(zip(('moneda', 'unidad', 'partida', 'capitulo', 'programa', 'subtitulo'), clave),
                           nombre_programa=g['nombre_programa'], montos=montos, diferencias=diferencias))
    return salida
