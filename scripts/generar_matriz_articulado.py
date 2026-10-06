"""
Generador de la Matriz Comparativa del Articulado Presupuestario (Ley 2026 vs Proyecto 2027).
Lee el dataset canónico revisado: ley 2026 oficial y copia local del proyecto 2027. La oficialidad de 2027 está pendiente.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DIST_DIR = BASE_DIR / "dist"
DOCS_DIR = BASE_DIR / "docs"

MATRIZ_ARTICULADO = json.loads((DATA_DIR / 'matriz_articulado_2026_2027.json').read_text(encoding='utf-8'))

def exportar_matriz():
    if len({r['id'] for r in MATRIZ_ARTICULADO}) != len(MATRIZ_ARTICULADO):
        raise ValueError('Ejes duplicados')
    for row in MATRIZ_ARTICULADO:
        if row['fuente_2026']['ley'] != '21.796' or not row['fuente_2027'].get('pagina'):
            raise ValueError('Falta evidencia normativa')
    for d in [DATA_DIR, DIST_DIR / "data", DOCS_DIR / "data"]:
        d.mkdir(parents=True, exist_ok=True)
        out_p = d / "matriz_articulado_2026_2027.json"
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(MATRIZ_ARTICULADO, f, ensure_ascii=False, indent=2)
        print(f"Matriz guardada en {out_p} ({len(MATRIZ_ARTICULADO)} ejes normativos)")

if __name__ == "__main__":
    exportar_matriz()
