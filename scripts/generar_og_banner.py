"""
Generador del banner OpenGraph (1200x630 px) para 'De la Glosa a la Calle'.
Estética: Azul Abisal (#04142b), acentos en cian (#38bdf8), dorado (#fbbf24) y terracota (#f97316).
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parents[1]

def crear_og_banner():
    ancho = 1200
    alto = 630
    
    # Crear imagen base con fondo Azul Abisal degradado
    img = Image.new("RGBA", (ancho, alto), (4, 20, 43, 255))
    draw = ImageDraw.Draw(img)
    
    # Gradiente sutil de fondo
    for y in range(alto):
        factor = y / alto
        r = int(4 + factor * 6)
        g = int(20 + factor * 12)
        b = int(43 + factor * 25)
        draw.line([(0, y), (ancho, y)], fill=(r, g, b, 255))
        
    # Marco sutil con borde institucional
    draw.rectangle([20, 20, ancho - 20, alto - 20], outline=(56, 189, 248, 80), width=2)
    draw.rectangle([24, 24, ancho - 24, alto - 24], outline=(251, 191, 36, 40), width=1)
    
    # Cargar fuentes del sistema o usar default
    try:
        font_eyebrow = ImageFont.truetype("arial.ttf", 24)
        font_title = ImageFont.truetype("arialbd.ttf", 64)
        font_sub = ImageFont.truetype("arial.ttf", 32)
        font_kpi_num = ImageFont.truetype("arialbd.ttf", 44)
        font_kpi_lbl = ImageFont.truetype("arial.ttf", 20)
        font_badge = ImageFont.truetype("arialbd.ttf", 18)
    except IOError:
        font_eyebrow = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_kpi_num = ImageFont.load_default()
        font_kpi_lbl = ImageFont.load_default()
        font_badge = ImageFont.load_default()

    # Badge superior: OBSERVATORIO FISCAL CIUDADANO
    draw.rounded_rectangle([70, 60, 460, 96], radius=8, fill=(15, 30, 60, 255), outline=(56, 189, 248, 180), width=1)
    draw.text((85, 68), "🏛️  OBSERVATORIO FISCAL CIUDADANO", fill=(56, 189, 248), font=font_badge)

    # Título Principal
    draw.text((70, 120), "DE LA GLOSA A LA CALLE", fill=(248, 250, 252), font=font_title)
    
    # Línea decorativa
    draw.line([(70, 205), (550, 205)], fill=(251, 191, 36), width=4)
    draw.line([(550, 205), (750, 205)], fill=(56, 189, 248), width=4)
    
    # Subtítulo y bajada editorial
    draw.text((70, 225), "Presupuesto de la Nación Chile 2027", fill=(56, 189, 248), font=font_sub)
    draw.text((70, 275), "¿Qué cambia de verdad entre la Ley 2026 y el Proyecto 2027?", fill=(203, 213, 225), font=font_sub)

    # 3 Tarjetas KPI
    kpis = [
        {"num": "$105,8 B", "lbl": "Gasto Fiscal Neto 2027", "col": (251, 191, 36), "x": 70},
        {"num": "515", "lbl": "Programas Comparados", "col": (56, 189, 248), "x": 430},
        {"num": "Radar Mixta", "lbl": "Seguimiento en Vivo Congreso", "col": (249, 115, 22), "x": 790},
    ]

    for kpi in kpis:
        x0 = kpi["x"]
        y0 = 360
        x1 = x0 + 340
        y1 = y0 + 150
        # Fondo tarjeta translúcido
        draw.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=(11, 26, 54, 230), outline=(51, 65, 85, 255), width=2)
        # Línea superior de color
        draw.line([(x0 + 12, y0 + 2), (x1 - 12, y0 + 2)], fill=kpi["col"], width=3)
        # Número y etiqueta
        draw.text((x0 + 24, y0 + 28), kpi["num"], fill=kpi["col"], font=font_kpi_num)
        draw.text((x0 + 24, y0 + 92), kpi["lbl"], fill=(226, 232, 240), font=font_kpi_lbl)

    # Footer institucional
    draw.text((70, 560), "delaglosaalacalle.evegat.cl  ·  Datos Oficiales DIPRES & Congreso Nacional", fill=(148, 163, 184), font=font_eyebrow)
    draw.text((950, 560), "Auditoría Cívica P149", fill=(148, 163, 184), font=font_eyebrow)

    # Convertir a RGB y guardar
    rgb_img = img.convert("RGB")
    
    destinos = [
        BASE / "dist/assets/og-preview.png",
        BASE / "docs/assets/og-preview.png",
    ]
    for d in destinos:
        d.parent.mkdir(parents=True, exist_ok=True)
        rgb_img.save(d, "PNG", optimize=True)
        print(f"Banner OpenGraph generado en: {d}")

if __name__ == "__main__":
    crear_og_banner()
