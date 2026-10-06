"""Compilación local sin acceso a red ni modificación de fuentes de datos."""
from pathlib import Path
import re
import shutil

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
    assets = dist / 'assets'
    assets.mkdir(exist_ok=True)
    for tag,extension in (('style','css'), ('script','js')):
        pattern = rf'<{tag}>(.*?)</{tag}>'
        blocks = re.findall(pattern,html,re.DOTALL)
        if blocks:
            (assets / f'relato.{extension}').write_text('\n'.join(blocks),encoding='utf-8')
            replacement = '<link rel="stylesheet" href="assets/relato.css">' if tag=='style' else '<script src="assets/relato.js" defer></script>'
            html = re.sub(pattern,replacement,html,count=1,flags=re.DOTALL)
    # Solo fuentes públicas ya presentes; no se exporta SQLite ni DuckDB.
    (dist / 'data').mkdir(exist_ok=True)
    for name in ('programas_evaluados_dipres.csv','costos_referencia.csv'):
        source = BASE / 'data' / name
        if source.is_file():shutil.copyfile(source,dist / 'data' / name)
    (dist / 'index.html').write_text(html, encoding='utf-8')

    # Si estamos compilando por defecto en deploy/, sincronizar docs/ para GitHub Pages
    if not destino:
        docs = BASE / 'docs'
        docs.mkdir(parents=True, exist_ok=True)
        (docs / 'assets').mkdir(exist_ok=True)
        shutil.copytree(assets, docs / 'assets', dirs_exist_ok=True, ignore=shutil.ignore_patterns('desktop.ini'))
        (docs / 'index.html').write_text(html, encoding='utf-8')
        (docs / '.nojekyll').touch()

        # Exportar datos estáticos completos
        try:
            import sys
            sys.path.insert(0, str(BASE / 'scripts'))
            from exportar_estatico import exportar_todo
            exportar_todo()
        except Exception as e:
            print(f'Aviso al exportar datos estáticos: {e}')

    return dist / 'index.html'


if __name__ == '__main__':
    print(f'Frontend compilado localmente: {compilar()}')

