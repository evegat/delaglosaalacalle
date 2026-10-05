"""Comparación por identidad presupuestaria; ausencias y procedencia explícitas.

No contiene una tasa IPC por defecto. El índice debe venir de una fuente oficial
contrastada por quien carga el dato. Un fixture no constituye evidencia oficial.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

CAMPOS = ('partida', 'capitulo', 'programa', 'subtitulo', 'item', 'asignacion')
ANCHOS = (2, 2, 2, 2, 2, 3)


def monto_decimal(valor):
    if valor is None or str(valor).strip().casefold() in {'', 'n/d', 'null', '-', '—'}:
        return None
    try:
        monto = Decimal(str(valor))
    except InvalidOperation:
        raise ValueError('Monto inválido') from None
    if not monto.is_finite() or monto < 0:
        raise ValueError('Monto inválido')
    return monto


def clave_completa(fila):
    partes = []
    for campo, ancho in zip(CAMPOS, ANCHOS):
        original = fila.get(campo, '')
        if isinstance(original, (int, float, Decimal)) and not isinstance(original, bool):
            numero = Decimal(str(original))
            if not numero.is_finite() or numero != numero.to_integral_value():
                raise ValueError(f'Código {campo} no integral')
            original = int(numero)
        valor = str(original).strip()
        if not valor.isascii() or not valor.isdigit() or len(valor) > ancho:
            raise ValueError(f'Código {campo} ausente o inválido')
        partes.append(valor.zfill(ancho))
    return tuple(partes)


@dataclass(frozen=True)
class IndiceIPC:
    indice_base: Decimal
    indice_objetivo: Decimal
    fuente: str
    periodo_base: str
    periodo_objetivo: str
    verificado: bool = False

    def factor(self, ano_base, ano_objetivo):
        host = urlparse(self.fuente).hostname or ''
        if not self.verificado or not (host == 'ine.gob.cl' or host.endswith('.ine.gob.cl')
                                     or host == 'ine.cl' or host.endswith('.ine.cl')):
            return None
        if (self.periodo_base, self.periodo_objetivo) != (str(ano_base), str(ano_objetivo)):
            return None
        a, b = monto_decimal(self.indice_base), monto_decimal(self.indice_objetivo)
        return b / a if a and b else None


def _indexar(filas):
    indice = {}
    for fila in filas:
        clave = clave_completa(fila)
        entrada = indice.setdefault(clave, {'montos': set(), 'unidades': set(), 'nombres': set()})
        entrada['montos'].add(monto_decimal(fila.get('monto')))
        entrada['unidades'].add((fila.get('moneda', 'CLP'), fila.get('unidad', 'pesos')))
        entrada['nombres'].add(str(fila.get('denominacion', '')))
    return indice


def comparar_presupuestos(base, objetivo, *, ano_base=2025, ano_objetivo=2026, ipc=None):
    """Unión externa determinista; nunca atribuye continuidad por el nombre."""
    if ano_objetivo <= ano_base:
        raise ValueError('Los ejercicios deben estar ordenados')
    bases, objetivos = _indexar(base), _indexar(objetivo)
    factor = ipc.factor(ano_base, ano_objetivo) if ipc else None
    salida = []
    for clave in sorted(bases.keys() | objetivos.keys()):
        a, b = bases.get(clave), objetivos.get(clave)
        ambiguo = any(x and (len(x['montos']) != 1 or len(x['unidades']) != 1) for x in (a, b))
        ma = next(iter(a['montos'])) if a and len(a['montos']) == 1 else None
        mb = next(iter(b['montos'])) if b and len(b['montos']) == 1 else None
        estado = 'comparable'
        if ambiguo: estado = 'ambiguo'
        elif not a or ma is None: estado = f'no_reportado_{ano_base}'
        elif not b or mb is None: estado = f'no_reportado_{ano_objetivo}'
        elif a['unidades'] != b['unidades']: estado = 'unidad_incompatible'
        elif ma == 0: estado = 'base_cero'
        elif mb == 0: estado = 'objetivo_cero_explicito'
        comparables = not ambiguo and ma is not None and mb is not None and a['unidades'] == b['unidades']
        nominal = (mb / ma - 1) * 100 if comparables and ma > 0 else None
        real = (mb / (ma * factor) - 1) * 100 if comparables and ma > 0 and mb > 0 and factor else None
        salida.append(dict(zip(CAMPOS, clave), **{
            f'monto_{ano_base}': ma, f'monto_{ano_objetivo}': mb,
            f'denominacion_{ano_base}': '; '.join(sorted(a['nombres'])) if a else None,
            f'denominacion_{ano_objetivo}': '; '.join(sorted(b['nombres'])) if b else None,
            'estado': estado, 'variacion_nominal_pct': nominal,
            'variacion_real_pct': real, 'fuente_ipc': ipc.fuente if real is not None else None,
            'motivo_real_no_disponible': None if real is not None else
                'Requiere ambos montos positivos, unidades comparables e IPC oficial verificado del período',
        }))
    return salida
