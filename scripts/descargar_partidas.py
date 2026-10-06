import urllib.request
import re

url = "https://presupuestokast.cl/partida/16"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req).read().decode("utf-8", errors="ignore")

js_url = "https://presupuestokast.cl/_astro/ArbolMinisterio.B9yJRdqb.js"
req_js = urllib.request.Request(js_url, headers={"User-Agent": "Mozilla/5.0"})
js_content = urllib.request.urlopen(req_js).read().decode("utf-8", errors="ignore")
print(f"Longitud de ArbolMinisterio.B9yJRdqb.js: {len(js_content)}")

matches = set(re.findall(r"fetch\([^)]+\)|/[a-zA-Z0-9_\-\./]+\.(?:json|parquet|csv)", js_content))
print("Patrones en JS:", matches)

# Buscar cadenas con comillas que tengan URLs o rutas
strings = set(re.findall(r"[\"'](/[a-zA-Z0-9_\-\./]+)[\"']", js_content))
print("Rutas relativas:", [s for s in strings if not s.endswith(".js") and not s.endswith(".css")])





