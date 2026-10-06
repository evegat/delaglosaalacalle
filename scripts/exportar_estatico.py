"""
Exportador de artefactos estáticos para GitHub Pages y CDN.
Genera los archivos JSON completos para funcionamiento 100% offline y estático en docs/ y dist/.
"""
import json
import csv
from io import StringIO
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DIST_DIR = BASE_DIR / "dist"
DOCS_DIR = BASE_DIR / "docs"

# Importar motor de bajada a la calle
import sys
sys.path.insert(0, str(BASE_DIR / "src"))
from bajada_calle import calcular_bajada_calle
from presupuesto_ciudadano import preparar_programas, resumen_presupuestario, construir_recorrido

def leer_csv(path):
    # UTF-8 primero; Latin-1 sólo si el archivo realmente no es UTF-8.
    try:
        text = path.read_text(encoding='utf-8-sig')
    except UnicodeDecodeError:
        text = path.read_text(encoding='latin1')
    return csv.DictReader(StringIO(text))

def exportar_todo():
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DIST_DIR / "data").mkdir(exist_ok=True)
    (DOCS_DIR / "data").mkdir(exist_ok=True)

    # 1. Cargar comparativa 2026-2027
    comp_path = DATA_DIR / "comparativa_programas_2026_2027.json"
    with open(comp_path, encoding="utf-8") as f:
        progs_2027 = json.load(f)

    progs_2027 = preparar_programas(progs_2027)
    presupuesto2027_payload = {**resumen_presupuestario(progs_2027), 'programas': progs_2027}

    # 2. Cargar catálogo de programas evaluados DIPRES
    prog_eval_path = DATA_DIR / "programas_evaluados_dipres.csv"
    programas_eval = []
    servicios_set = set()
    if prog_eval_path.is_file():
        if prog_eval_path.is_file():
            reader = leer_csv(prog_eval_path)
            for r in reader:
                p_item = {
                    "id_bips": r.get("id_bips") or r.get("id"),
                    "ministerio": r.get("ministerio"),
                    "servicio": r.get("servicio"),
                    "nombre_programa": r.get("nombre_programa"),
                    "presupuesto_2026_m$": float(r.get("presupuesto_2026_m$") or 0) if r.get("presupuesto_2026_m$") else None,
                    "variacion_pct": float(r.get("variacion_presupuesto_2025_2026_pct") or 0) if r.get("variacion_presupuesto_2025_2026_pct") else None,
                    "descripcion": r.get("descripcion") or r.get("antecedentes_generales")
                }
                programas_eval.append(p_item)
                if r.get("servicio"):
                    servicios_set.add(r.get("servicio").strip())

    servicios_list = sorted(list(servicios_set))

    # 3. Cargar costos de referencia
    costos_path = DATA_DIR / "costos_referencia.csv"
    equivalencias_grupos = []
    if costos_path.is_file():
        if costos_path.is_file():
            reader = leer_csv(costos_path)
            for r in reader:
                equivalencias_grupos.append({
                    "servicio": r.get("servicio"),
                    "territorio": r.get("territorio"),
                    "periodo": r.get("periodo"),
                    "n": int(r.get("n") or 0),
                    "unidad": r.get("unidad"),
                    "moneda": r.get("moneda"),
                    "p25": float(r.get("p25") or 0) if r.get("p25") else None,
                    "p50": float(r.get("p50") or 0) if r.get("p50") else None,
                    "p75": float(r.get("p75") or 0) if r.get("p75") else None,
                    "desviacion_estandar": float(r.get("desviacion_estandar") or 0) if r.get("desviacion_estandar") else None,
                    "limite": r.get("limite") or "Muestra observacional ChileCompra"
                })

    equivalencias_payload = {
        "limite_metodologico": "Muestras territoriales observacionales. No imputan precios cero ni predicen costos fijos futuros.",
        "grupos": equivalencias_grupos
    }

    # 4. Generar Diccionario Consolidado de Recorridos (Drawer)
    recorridos_dict = {}
    for p in progs_2027:
        rec_obj = construir_recorrido(p)
        recorridos_dict[p.get("codigo")] = rec_obj
        recorridos_dict[p.get("nombre_programa")] = rec_obj
        recorridos_dict[p.get("nombre_programa").casefold()] = rec_obj

    # También agregar los programas evaluados BIPS
    for pe in programas_eval:
        b_mock = calcular_bajada_calle({"nombre_programa": pe["nombre_programa"], "partida": "09", "dif_vs_ini_mclp": 0, "proy_2027_mclp": pe["presupuesto_2026_m$"]})
        estaciones_bips = [
            {
                "estacion": 1,
                "fase": "Origen Fiscal",
                "titulo": pe.get("ministerio") or "Ministerio",
                "detalle": f"Servicio: {pe.get('servicio')} · Programa: {pe.get('nombre_programa')}",
                "tipo": "institucional"
            },
            {
                "estacion": 2,
                "fase": "Mecanismo Presupuestario",
                "titulo": f"Presupuesto Base 2026: ${pe.get('presupuesto_2026_m$', 0) or 0:,.0f} M$",
                "detalle": f"Variación declarada: {pe.get('variacion_pct') or 0}%",
                "tipo": "normativo"
            },
            {
                "estacion": 3,
                "fase": "Gestión y Compras Públicas",
                "titulo": b_mock["organismo"] if b_mock else (pe.get("servicio") or "Servicio Ejecutor"),
                "detalle": f"Referencia: {b_mock['contrato_ref']}" if b_mock else "Convenio de Gestión Directa / Mercado Público",
                "tipo": "operacional"
            },
            {
                "estacion": 4,
                "fase": "En la Calle",
                "titulo": b_mock["impacto_texto"] if b_mock else "Servicios directos a la ciudadanía",
                "costo_unitario_referencia": b_mock["costo_unitario_clp"] if b_mock else None,
                "dilema_calle": b_mock["dilema"] if b_mock else "Continuidad operacional y calidad de atención en el territorio.",
                "tipo": "calle"
            }
        ]
        rec_bips = {
            "programa": {
                "nombre_programa": pe.get("nombre_programa"),
                "servicio": pe.get("servicio"),
                "ministerio": pe.get("ministerio"),
                "presupuesto_2026_m$": pe.get("presupuesto_2026_m$"),
                "variacion_pct": pe.get("variacion_pct"),
                "descripcion": pe.get("descripcion") or "Ficha de evaluación de programas públicos BIPS / DIPRES."
            },
            "bajada_calle": b_mock,
            "estaciones": estaciones_bips
        }
        if pe.get("id_bips"):
            recorridos_dict[str(pe["id_bips"])] = rec_bips
        if pe.get("nombre_programa"):
            recorridos_dict[pe["nombre_programa"]] = rec_bips
            recorridos_dict[pe["nombre_programa"].casefold()] = rec_bips

    # Comparación base 2025 vs 2026
    comparacion_payload = {
        "origen": "dipres_ley_inicial",
        "motivo": "Comparación multianual con identidad de seis códigos presupuestarios DIPRES.",
        "datos": []
    }

    # Guardar en dist/data y docs/data
    archivos_json = {
        "presupuesto2027.json": presupuesto2027_payload,
        "programas.json": programas_eval,
        "servicios.json": servicios_list,
        "equivalencias.json": equivalencias_payload,
        "comparacion.json": comparacion_payload,
        "recorridos.json": recorridos_dict
    }

    for dir_destino in [DIST_DIR, DOCS_DIR]:
        for nombre, obj in archivos_json.items():
            dest = dir_destino / "data" / nombre
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
            print(f"Generado {dest} ({dest.stat().st_size:,} bytes)")

        # Copiar CSV públicos y matrices para descarga directa
        for data_file in ["programas_evaluados_dipres.csv", "costos_referencia.csv", "matriz_articulado_2026_2027.json"]:
            src = DATA_DIR / data_file
            if src.is_file():
                shutil.copyfile(src, dir_destino / "data" / data_file)

        # Generar artefactos para consumo por Agentes de IA y LLMs (llms.txt, openapi.json, prompt_agente.md)
        llms_txt_content = """# De la Glosa a la Calle: Presupuesto Público 2027 vs 2026

> Observatorio ciudadano determinista de análisis presupuestario del sector público chileno y su traducción a magnitudes comprensibles en compras públicas.
> URL Producción: https://evegat.github.io/delaglosaalacalle/
> Repositorio GitHub: https://github.com/evegat/delaglosaalacalle

## Directrices para Agentes de Inteligencia Artificial (LLMs)
- Unidades monetarias: Miles de pesos chilenos (M$ CLP) y millones de USD según se indique.
- Fuentes oficiales:
  - Ley Inicial y Vigente 2026: Ley N° 21.796 (DIPRES).
  - Proyecto de Presupuestos 2027: Mensaje Presidencial N° 180 (Cámara de Diputadas y Diputados).
- Criterios de rigurosidad presupuestaria:
  1. Una variación presupuestaria NO demuestra por sí sola prestaciones efectivamente perdidas ni territorialidad exacta.
  2. Los programas sin contraparte identificada en 2026 tienen base NULL (no imputar falso cero).
  3. No generalizar compras de un ministerio a otro (los computadores sólo aplican a programas de tecnología escolar como Becas TIC).
  4. Endeudamiento (Artículo 3): Propone elevar el techo de deuda de US$ 17.400M a US$ 25.000M (+43,7% / +US$ 7.600M). Es una autorización máxima de endeudamiento para el ejercicio, no deuda emitida.
  5. SLEP (Artículo 40): Reitera la suspensión del traspaso de 5 SLEP (Litoral, Los Cerezos, Los Copihues, Chacabuco y Los Viñedos), la cual ya estaba vigente en 2026 bajo el Art. 41 de la Ley 21.796.

## Datasets Estructurados Disponibles (JSON y CSV)
- [Presupuesto 2027 vs 2026 (JSON)](https://evegat.github.io/delaglosaalacalle/data/presupuesto2027.json): 266 programas presupuestarios en 6 carteras clave (Salud, Educación, Vivienda, Interior, Culturas y GOREs) con base inicial 2026, vigente 2026, proyecto 2027 y variaciones.
- [Matriz de Articulado Normativo (JSON)](https://evegat.github.io/delaglosaalacalle/data/matriz_articulado_2026_2027.json): 9 ejes normativos críticos (deuda, suspensión SLEP, cobro ejecutivo SEP con embargo, tope a honorarios, blindaje fundaciones anti Convenios, trato directo en obras, pago a proveedores, publicidad estatal y plataforma transaccional).
- [Recorridos de la Glosa a la Calle (JSON)](https://evegat.github.io/delaglosaalacalle/data/recorridos.json): Fichas de transformación fiscal: Origen institucional -> Mecanismo (Subtítulo) -> Ejecución -> Impacto de calle.
- [Catálogo de Programas Evaluados DIPRES (CSV)](https://evegat.github.io/delaglosaalacalle/data/programas_evaluados_dipres.csv): 166 programas evaluados con código BIPS, descripción oficial y motivos de variación presupuestaria.
- [Costos de Referencia en Mercado Público (CSV)](https://evegat.github.io/delaglosaalacalle/data/costos_referencia.csv): Muestras observacionales con cuartiles P25, P50, P75 y contratos de referencia.

## Integración con Agentes y Custom GPTs
- [Especificación OpenAPI 3.1.0](https://evegat.github.io/delaglosaalacalle/openapi.json): Importable directamente como 'Action' en Custom GPTs de ChatGPT o como herramienta de consulta en frameworks de agentes.
- [Prompt de Asistente Presupuestario](https://evegat.github.io/delaglosaalacalle/prompt_agente.md): Instrucciones listas para copiar y pegar en ChatGPT, Claude o Gemini.
"""
        (dir_destino / "llms.txt").write_text(llms_txt_content, encoding="utf-8")

        openapi_spec = {
            "openapi": "3.1.0",
            "info": {
                "title": "De la Glosa a la Calle API",
                "description": "Catálogo determinista de datos abiertos del Presupuesto Público de Chile 2027 vs 2026.",
                "version": "2.0.0"
            },
            "servers": [
                {
                    "url": "https://evegat.github.io/delaglosaalacalle",
                    "description": "Servidor Público de Datos (GitHub Pages CDN)"
                }
            ],
            "paths": {
                "/data/presupuesto2027.json": {
                    "get": {
                        "operationId": "obtenerPresupuesto2027",
                        "summary": "Obtiene la comparativa completa de 266 programas presupuestarios 2026 vs 2027",
                        "description": "Retorna totales consolidados y detalle de 266 programas (Salud, Educación, Vivienda, Interior, Culturas y GOREs) con montos inicial 2026, vigente 2026 y proyecto 2027 en miles de pesos.",
                        "responses": {
                            "200": {
                                "description": "Resumen y lista de programas presupuestarios",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                },
                "/data/matriz_articulado_2026_2027.json": {
                    "get": {
                        "operationId": "obtenerMatrizArticulado",
                        "summary": "Obtiene los 9 ejes normativos del articulado (Ley 2026 vs Proyecto 2027)",
                        "description": "Contraste normativo riguroso entre la Ley N° 21.796 y el Mensaje N° 180 (endeudamiento, SLEP, SEP, honorarios, fundaciones, obras, proveedores, publicidad, transparencia).",
                        "responses": {
                            "200": {
                                "description": "Lista de ejes normativos comparados",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "array"}
                                    }
                                }
                            }
                        }
                    }
                },
                "/data/recorridos.json": {
                    "get": {
                        "operationId": "obtenerRecorridosGasto",
                        "summary": "Obtiene los recorridos de gasto desde la glosa hasta la calle",
                        "description": "Diccionario indexado por código de programa y BIPS con las 4 estaciones de ejecución fiscal y compras públicas.",
                        "responses": {
                            "200": {
                                "description": "Mapa de recorridos",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        with open(dir_destino / "openapi.json", "w", encoding="utf-8") as f:
            json.dump(openapi_spec, f, ensure_ascii=False, indent=2)

        prompt_agente_content = """# Prompt de Asistente Ciudadano de Presupuesto Público (P149)

Puedes copiar y pegar este prompt en **ChatGPT**, **Claude**, **Gemini** o tu agente favorito para convertirlo en un experto riguroso sobre el Presupuesto 2027:

```markdown
Eres un asistente cívico riguroso especializado en el Presupuesto Público de Chile 2027 y su comparativa frente a la Ley 2026.
Toda tu información proviene de datos oficiales auditados por el proyecto 'De la Glosa a la Calle' (https://evegat.github.io/delaglosaalacalle/).

Instrucciones de consulta:
1. Para responder dudas de programas y cifras, consulta los datos estructurados en:
   https://evegat.github.io/delaglosaalacalle/data/presupuesto2027.json
2. Para dudas normativas y de leyes (endeudamiento, SLEP, fundaciones, honorarios), consulta:
   https://evegat.github.io/delaglosaalacalle/data/matriz_articulado_2026_2027.json
3. Reglas metodológicas obligatorias:
   - Los montos están en miles de pesos chilenos (M$ CLP).
   - Base 2026: Ley N° 21.796 (DIPRES).
   - Proyecto 2027: Mensaje Presidencial N° 180 (Cámara de Diputadas y Diputados).
   - El endeudamiento fiscal propuesto en el Art. 3 sube de US$ 17.400M a US$ 25.000M (+43,7%).
   - La suspensión de 5 SLEP (Art. 40) ya existía en 2026 (Art. 41 de Ley 21.796).
   - Una variación presupuestaria NO demuestra por sí sola servicios o prestaciones perdidas en terreno.
   - Cita siempre la fuente y el enlace de consulta de https://evegat.github.io/delaglosaalacalle/
```
"""
        (dir_destino / "prompt_agente.md").write_text(prompt_agente_content, encoding="utf-8")

    print(f"Exportación estática completada para {len(progs_2027)} programas 2027 y {len(programas_eval)} evaluados.")
    print("Artefactos para Agentes de IA generados: llms.txt, openapi.json, prompt_agente.md")

if __name__ == "__main__":
    exportar_todo()

