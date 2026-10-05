"""Compilación local sin acceso a red ni modificación de fuentes de datos."""
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def compilar(destino=None):
    template = BASE / 'src/interfaz.html'
    if not template.is_file():
        raise ValueError('Falta la plantilla editable src/interfaz.html')
    html = template.read_text(encoding='utf-8')
    if '<html' not in html or '</html>' not in html:
        raise ValueError('Plantilla HTML incompleta')
    dist = Path(destino) if destino else BASE / 'dist'
    dist.mkdir(parents=True, exist_ok=True)
    (dist / 'index.html').write_text(html, encoding='utf-8')
    return dist / 'index.html'


if __name__ == '__main__':
    print(f'Frontend compilado localmente: {compilar()}')
