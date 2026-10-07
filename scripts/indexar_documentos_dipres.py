"""Indexar todos los documentos descargados de DIPRES 2027 en un catálogo estructurado (JSON, CSV, DuckDB)."""
from pathlib import Path
import json
import csv
import re

DIR_DOCS = Path(r"c:\Users\evega\OneDrive\Documents\Obsidian\MyWorld\2 - Project\P149 - De la Glosa a la Calle\data\dipres_2027_oficial")
SALIDA_JSON = Path(r"c:\Users\evega\OneDrive\Documents\Obsidian\MyWorld\2 - Project\P149 - De la Glosa a la Calle\data\indice_documentos_dipres_2027.json")
SALIDA_CSV = Path(r"c:\Users\evega\OneDrive\Documents\Obsidian\MyWorld\2 - Project\P149 - De la Glosa a la Calle\data\indice_documentos_dipres_2027.csv")

def indexar():
    if not DIR_DOCS.exists():
        print("Directorio de documentos no existe.")
        return

    archivos = list(DIR_DOCS.glob("*.*"))
    print(f"Indexando {len(archivos)} documentos...")

    registros = []
    for f in sorted(archivos, key=lambda x: x.name):
        nombre = f.name
        size_bytes = f.stat().st_size
        ext = f.suffix.lower().lstrip(".")
        
        # Categorizar documento
        categoria = "general"
        if "acta" in nombre or "comite" in nombre or "pib" in nombre or "cobre" in nombre:
            categoria = "macro_supuestos"
        elif "426556" in nombre:
            categoria = "mensaje_presidencial_articulado"
        elif "433297" in nombre:
            categoria = "informe_finanzas_publicas_ifp"
        elif "433300" in nombre:
            categoria = "folleto_prioridades"
        elif "433302" in nombre or "433301" in nombre:
            categoria = "oferta_programatica"
        elif "430808" in nombre:
            categoria = "presupuesto_nacional_consolidado"
        elif "doc_pdf" in nombre:
            categoria = "detalle_partida_capitulo_pdf"
        elif "doc_xls" in nombre or "xlsx" in ext:
            categoria = "detalle_partida_capitulo_excel"

        registros.append({
            "archivo": nombre,
            "categoria": categoria,
            "tipo_archivo": ext,
            "tamano_bytes": size_bytes,
            "tamano_kb": round(size_bytes / 1024, 1),
            "ruta_relativa": f"data/dipres_2027_oficial/{nombre}"
        })

    # Guardar JSON
    with open(SALIDA_JSON, "w", encoding="utf-8") as jf:
        json.dump({
            "total_documentos": len(registros),
            "fuente_oficial": "Dirección de Presupuestos (DIPRES) - Ministerio de Hacienda",
            "periodo": "Proyecto de Presupuestos 2027",
            "documentos": registros
        }, jf, ensure_ascii=False, indent=2)

    # Guardar CSV
    with open(SALIDA_CSV, "w", encoding="utf-8", newline="") as cf:
        writer = csv.DictWriter(cf, fieldnames=["archivo", "categoria", "tipo_archivo", "tamano_bytes", "tamano_kb", "ruta_relativa"])
        writer.writeheader()
        writer.writerows(registros)

    print(f"Catálogo generado con éxito: {len(registros)} documentos en {SALIDA_JSON.name} y {SALIDA_CSV.name}")

if __name__ == "__main__":
    indexar()
