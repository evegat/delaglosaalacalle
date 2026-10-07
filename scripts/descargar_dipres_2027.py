"""Script para descargar todos los antecedentes y documentos oficiales del Presupuesto 2027 desde DIPRES."""
import re
import urllib.request
from pathlib import Path

DESTINO = Path(r"c:\Users\evega\OneDrive\Documents\Obsidian\MyWorld\2 - Project\P149 - De la Glosa a la Calle\data\dipres_2027_oficial")
DESTINO.mkdir(parents=True, exist_ok=True)

URLS_BASE = [
    "https://www.dipres.gob.cl/597/w3-multipropertyvalues-15199-38403.html",  # Antecedentes
    "https://www.dipres.gob.cl/597/w3-multipropertyvalues-15168-38403.html",  # Proyecto Ley Nacional
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def extraer_enlaces():
    enlaces = set()
    for u in URLS_BASE:
        req = urllib.request.Request(u, headers=HEADERS)
        try:
            with urllib.request.urlopen(req) as r:
                html = r.read().decode("utf-8", errors="ignore")
                matches = re.findall(r'href=["\'](articles-[^"\']+\.(?:pdf|xlsx|csv|xml))(?:\?[^"\']*)?["\']', html)
                for m in matches:
                    enlaces.add(m)
        except Exception as e:
            print(f"Error leyendo {u}: {e}")
    return sorted(enlaces)

def descargar():
    enlaces = extraer_enlaces()
    print(f"Total documentos encontrados: {len(enlaces)}")
    base_dipres = "https://www.dipres.gob.cl/597/"
    for rel in enlaces:
        target = DESTINO / rel
        url = base_dipres + rel
        if target.exists() and target.stat().st_size > 0:
            print(f"Ya existe: {rel} ({target.stat().st_size} bytes)")
            continue
        print(f"Descargando {rel}...")
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req) as r:
                target.write_bytes(r.read())
            print(f"Guardado: {rel} ({target.stat().st_size} bytes)")
        except Exception as e:
            print(f"Fallo descarga {rel}: {e}")

if __name__ == "__main__":
    descargar()
