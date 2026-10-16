"""Compilación local sin acceso a red ni modificación de fuentes de datos."""
from pathlib import Path
import re
import shutil
import subprocess
import sys

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
            (assets / f'relato_v240.{extension}').write_text('\n'.join(blocks),encoding='utf-8')
            replacement = '<link rel="stylesheet" href="assets/relato_v240.css">' if tag=='style' else '<script src="assets/relato_v240.js" defer></script>'
            html = re.sub(pattern,replacement,html,count=1,flags=re.DOTALL)
    # Solo fuentes públicas ya presentes; no se exporta SQLite ni DuckDB.
    (dist / 'data').mkdir(exist_ok=True)
    archivos_data = (
        'programas_evaluados_dipres.csv',
        'costos_referencia.csv',
        'indice_documentos_dipres_2027.json',
        'indice_documentos_dipres_2027.csv',
        'comision_mixta_hitos.json',
    )
    for name in archivos_data:
        source = BASE / 'data' / name
        if source.is_file():
            shutil.copyfile(source, dist / 'data' / name)
    # Generar robots.txt y sitemap.xml para SEO y crawlers
    robots_content = "User-agent: *\nAllow: /\n\nSitemap: https://delaglosaalacalle.evegat.cl/sitemap.xml\n"
    sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://delaglosaalacalle.evegat.cl/</loc>
    <lastmod>2026-10-10</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://delaglosaalacalle.evegat.cl/#comparacion</loc>
    <lastmod>2026-10-10</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://delaglosaalacalle.evegat.cl/#seccion-macro</loc>
    <lastmod>2026-10-10</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://delaglosaalacalle.evegat.cl/#seccion-mixta</loc>
    <lastmod>2026-10-10</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://delaglosaalacalle.evegat.cl/#recorridos</loc>
    <lastmod>2026-10-10</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://delaglosaalacalle.evegat.cl/#articulado</loc>
    <lastmod>2026-10-10</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://delaglosaalacalle.evegat.cl/#evaluaciones</loc>
    <lastmod>2026-10-10</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>
</urlset>
"""
    (dist / 'robots.txt').write_text(robots_content, encoding='utf-8')
    (dist / 'sitemap.xml').write_text(sitemap_content, encoding='utf-8')

    # Generar o sincronizar banner OpenGraph si existe el script
    og_script = BASE / 'scripts/generar_og_banner.py'
    if og_script.is_file():
        import subprocess
        subprocess.run([sys.executable, str(og_script)], check=False)

    (dist / 'index.html').write_text(html, encoding='utf-8')
    (dist / 'CNAME').write_text('delaglosaalacalle.evegat.cl', encoding='utf-8')

    # Si estamos compilando por defecto en deploy/, sincronizar docs/ para GitHub Pages
    if not destino:
        docs = BASE / 'docs'
        docs.mkdir(parents=True, exist_ok=True)
        (docs / 'assets').mkdir(exist_ok=True)
        shutil.copytree(assets, docs / 'assets', dirs_exist_ok=True, ignore=shutil.ignore_patterns('desktop.ini'))
        (docs / 'index.html').write_text(html, encoding='utf-8')
        (docs / '.nojekyll').touch()
        (docs / 'CNAME').write_text('delaglosaalacalle.evegat.cl', encoding='utf-8')
        (docs / 'robots.txt').write_text(robots_content, encoding='utf-8')
        (docs / 'sitemap.xml').write_text(sitemap_content, encoding='utf-8')
        (docs / 'data').mkdir(exist_ok=True)
        for name in archivos_data:
            source = BASE / 'data' / name
            if source.is_file():
                shutil.copyfile(source, docs / 'data' / name)

        # Exportar datos estáticos completos
        if str(BASE / 'scripts') not in sys.path:
            sys.path.insert(0, str(BASE / 'scripts'))
        from exportar_estatico import exportar_todo
        exportar_todo()

    return dist / 'index.html'


if __name__ == '__main__':
    print(f'Frontend compilado localmente: {compilar()}')

