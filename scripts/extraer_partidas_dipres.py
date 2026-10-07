"""Descargar todos los apéndices de partidas, capítulos y programas de DIPRES 2027."""
import re
import urllib.request
from pathlib import Path

DESTINO = Path(r"c:\Users\evega\OneDrive\Documents\Obsidian\MyWorld\2 - Project\P149 - De la Glosa a la Calle\data\dipres_2027_oficial")
DESTINO.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

html_path = Path(r"C:\Users\evega\.gemini\antigravity\brain\2d1f9403-3dfe-4bc9-8859-cee572298488\.system_generated\steps\500\content.md")
content = html_path.read_text(encoding="utf-8")

# buscar links rel=appendix
pattern = r'<link[^>]+>'
tags = re.findall(pattern, content)
appendix_hrefs = []
for t in tags:
    if 'appendix' in t:
        m = re.search(r'href=[\"\']([^\"\']+)[\"\']', t)
        if m:
            appendix_hrefs.append(m.group(1))

print("Apéndices encontrados:", appendix_hrefs)

base_dipres = "https://www.dipres.gob.cl/597/"
todos_enlaces = set()

for app in appendix_hrefs:
    u = base_dipres + app
    print("Leyendo apéndice:", u)
    try:
        req = urllib.request.Request(u, headers=HEADERS)
        with urllib.request.urlopen(req) as r:
            sub_html = r.read().decode("utf-8", errors="ignore")
            # Buscar links a archivos
            files = re.findall(r'href=["\'](articles-[^"\']+\.(?:pdf|xlsx|csv|xml))(?:\?[^"\']*)?["\']', sub_html)
            for f in files:
                todos_enlaces.add(f)
            print(f"  Encontrados {len(files)} enlaces en {app}")
    except Exception as e:
        print(f"Error leyendo {u}: {e}")

print(f"Total archivos encontrados en apéndices: {len(todos_enlaces)}")

for rel in sorted(todos_enlaces):
    target = DESTINO / rel
    if target.exists() and target.stat().st_size > 0:
        continue
    url = base_dipres + rel
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req) as r:
            target.write_bytes(r.read())
        print(f"Guardado: {rel} ({target.stat().st_size} bytes)")
    except Exception as e:
        print(f"Error descargando {rel}: {e}")
