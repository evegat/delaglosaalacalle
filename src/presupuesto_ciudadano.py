"""Comparaciones nominales por programa; ausencia distinta de cero."""
from copy import deepcopy

try:
    from .bajada_calle import calcular_bajada_calle
except ImportError:
    from bajada_calle import calcular_bajada_calle


def preparar_programas(datos):
    rows = deepcopy(datos)
    for row in rows:
        proyecto = row.get('proy_2027_mclp')
        for base, sufijo in [('ini_2026_mclp', 'ini'), ('vig_2026_mclp', 'vig')]:
            valor = row.get(base)
            disponible = valor is not None and proyecto is not None
            row[f'dif_vs_{sufijo}_mclp'] = proyecto - valor if disponible else None
            row[f'pct_vs_{sufijo}'] = round((proyecto / valor - 1) * 100, 2) if disponible and valor > 0 else None
        row['estado_base_2026'] = 'disponible' if row.get('ini_2026_mclp') is not None else 'sin_contraparte_identificada'
        row['bajada_calle'] = calcular_bajada_calle(row)
    return rows


def resumen_presupuestario(rows):
    def total(campo, seleccion):
        valores = [r[campo] for r in seleccion if r.get(campo) is not None]
        return sum(valores) if valores else None

    comparables = {}
    for nombre, campo in [('inicial', 'ini_2026_mclp'), ('vigente', 'vig_2026_mclp')]:
        pares = [r for r in rows if r.get(campo) is not None and r.get('proy_2027_mclp') is not None]
        base = total(campo, pares)
        proyecto = total('proy_2027_mclp', pares)
        comparables[nombre] = {
            'total_programas': len(pares), 'base_2026_mclp': base, 'proyecto_2027_mclp': proyecto,
            'diferencia_mclp': proyecto - base if base is not None else None,
            'variacion_pct': round((proyecto / base - 1) * 100, 2) if base is not None and base > 0 else None,
        }
    return {
        'total_programas': len(rows),
        'totales_mclp': {
            'inicial_2026': total('ini_2026_mclp', rows), 'vigente_2026': total('vig_2026_mclp', rows),
            'proyecto_2027': total('proy_2027_mclp', rows),
            'dif_vs_ini': comparables['inicial']['diferencia_mclp'],
            'dif_vs_vig': comparables['vigente']['diferencia_mclp'],
        },
        'comparables': comparables,
        'cobertura': {
            'sin_base_inicial': sum(r.get('ini_2026_mclp') is None for r in rows),
            'sin_base_vigente': sum(r.get('vig_2026_mclp') is None for r in rows),
            'sin_proyecto_2027': sum(r.get('proy_2027_mclp') is None for r in rows),
            'fuente_2027_secundaria': sum(r.get('fuente_2027', {}).get('autoridad') == 'secundaria' for r in rows),
        },
        'metodo': 'M$ nominales; diferencias sobre los mismos códigos con ambos valores disponibles. '
                  'Códigos iguales no prueban perímetros institucionales equivalentes. '
                  'Suma de programas, no gasto público consolidado. No demuestra prestaciones perdidas.',
    }


def detalle_variacion(row):
    diferencia = row.get('dif_vs_ini_mclp')
    if diferencia is None:
        return 'Sin base 2026 identificada; variación no disponible.'
    porcentaje = row.get('pct_vs_ini')
    pct = f'{porcentaje}%' if porcentaje is not None else 'porcentaje no calculable con base cero'
    return f'Variación nominal vs Inicial 2026: {pct} (Dif: ${diferencia:,} M$).'


def construir_recorrido(row):
    bajada = row.get('bajada_calle') or calcular_bajada_calle(row)
    proyecto = row.get('proy_2027_mclp')
    cod = row.get('codigo')
    nombre_prog = row.get('nombre_programa')
    desc = f"Programa presupuestario {cod}"
    if cod == '09-09-03':
        nombre_prog = f"{nombre_prog} (Becas TIC · Yo Elijo Mi PC)"
        desc = "Financia la entrega de computadores personales y conectividad a internet para estudiantes de 7° básico (Programa Becas TIC / Yo Elijo Mi PC / Me Conecto para Aprender), además de becas de mantención y apoyo a la retención escolar."
    return {
        'programa': {
            'nombre_programa': nombre_prog, 'servicio': row.get('nombre_capitulo'),
            'ministerio': row.get('nombre_partida'), 'presupuesto_2026_m$': row.get('ini_2026_mclp'),
            'variacion_pct': row.get('pct_vs_ini'), 'descripcion': desc,
        },
        'bajada_calle': bajada,
        'fuente_2027': row.get('fuente_2027'),
        'estaciones': [
            {'estacion': 1, 'fase': 'Origen Fiscal', 'titulo': row.get('nombre_partida'),
             'detalle': f"Capítulo: {row.get('nombre_capitulo')} · Programa: {row.get('nombre_programa')}", 'tipo': 'institucional'},
            {'estacion': 2, 'fase': 'Mecanismo Presupuestario',
             'titulo': f'Presupuesto 2027: ${proyecto:,} M$' if proyecto is not None else 'Proyecto 2027 no disponible',
             'detalle': detalle_variacion(row), 'regla_ejecucion': 'Propuesta presupuestaria 2027', 'tipo': 'normativo'},
            {'estacion': 3, 'fase': 'Gestión y Compras Públicas',
             'titulo': bajada['organismo'] if bajada else row.get('nombre_capitulo'),
             'detalle': f"Referencia de costo no verificada: {bajada['contrato_ref']}" if bajada else 'Compra específica no identificada', 'tipo': 'operacional'},
            {'estacion': 4, 'fase': 'En la Calle', 'titulo': bajada['impacto_texto'] if bajada else 'Sin equivalencia calculable',
             'costo_unitario_referencia': bajada['costo_unitario_clp'] if bajada else None,
             'dilema_calle': bajada['limite_metodologico'] if bajada else 'Sin datos suficientes para imputar prestaciones o pérdida territorial.', 'tipo': 'calle'},
        ],
    }
