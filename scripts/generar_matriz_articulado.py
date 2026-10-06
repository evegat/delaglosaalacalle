"""
Generador de la Matriz Comparativa del Articulado Presupuestario (Ley 2026 vs Proyecto 2027).
Basado en el texto oficial del Mensaje N° 180 (Cámara de Diputadas y Diputados).
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DIST_DIR = BASE_DIR / "dist"
DOCS_DIR = BASE_DIR / "docs"

MATRIZ_ARTICULADO = [
    {
        "id": "art-03-deuda",
        "eje": "Macroeconomía y Endeudamiento",
        "articulo": "Artículo 3",
        "titulo": "Techo de Endeudamiento Fiscal",
        "nivel_cambio": "Crítico",
        "tipo_cambio": "Aumento Sustantivo (+51,5%)",
        "norma_2026": "Autorizaba al Presidente para contraer endeudamiento hasta por US$ 16.500 millones para el ejercicio presupuestario.",
        "norma_2027": "Eleva la autorización de endeudamiento fiscal hasta por US$ 25.000 millones (incluyendo amortizaciones e intereses en Ingresos Generales de la Nación).",
        "impacto_calle": "Autoriza al Fisco a emitir US$ 8.500 millones más en deuda que en 2026. Es el eje central del debate legislativo por su impacto en la sostenibilidad de las finanzas públicas y el pago de intereses futuros.",
        "icono": "📈"
    },
    {
        "id": "art-40-slep",
        "eje": "Educación Pública",
        "articulo": "Artículo 40",
        "titulo": "Freno al Traspaso de Colegios a los SLEP",
        "nivel_cambio": "Crítico",
        "tipo_cambio": "Suspensión de Desmunicipalización",
        "norma_2026": "Continuidad del cronograma de traspaso gradual de colegios municipales a los Servicios Locales de Educación Pública (Ley 21.040).",
        "norma_2027": "Establece perentoriamente que el traspaso educacional a los SLEP Litoral, Los Cerezos, Los Copihues, Chacabuco y Los Viñedos 'no se producirá el año 2027'.",
        "impacto_calle": "Se congela la desmunicipalización en decenas de comunas. Los municipios deben seguir administrando y financiando los colegios durante 2027, suspendiendo la absorción estatal de nóminas e infraestructura.",
        "icono": "🏫"
    },
    {
        "id": "art-44-sep",
        "eje": "Educación Pública",
        "articulo": "Artículo 44",
        "titulo": "Recuperación de Saldos SEP con Mérito Ejecutivo",
        "nivel_cambio": "Mayor",
        "tipo_cambio": "Cobro Judicial y Embargo",
        "norma_2026": "Rendición de saldos de Subvención Escolar Preferencial (SEP) mediante procedimientos administrativos ordinarios de la Superintendencia de Educación.",
        "norma_2027": "Obliga a sostenedores y municipios a presentar un 'Plan de Recuperación de Saldos' al 30 de abril 2027. Ante incumplimiento, reintegro en 1 cuota al 30 de junio 2028 y resoluciones con mérito ejecutivo ante tribunales ordinarios.",
        "impacto_calle": "Faculta al Mineduc a demandar ejecutivamente (con embargo de cuentas o bienes) a corporaciones municipales y sostenedores que mantengan platas SEP sin justificar.",
        "icono": "⚖️"
    },
    {
        "id": "art-15-honorarios",
        "eje": "Empleo Público y Gestión",
        "articulo": "Artículo 15",
        "titulo": "Tope Estricto de Traspaso a Contrata",
        "nivel_cambio": "Mayor",
        "tipo_cambio": "Restricción Numérica",
        "norma_2026": "Permitía traspasos masivos de honorarios a contrata para cumplir con los dictámenes de la Contraloría sobre 'confianza legítima' y funciones permanentes.",
        "norma_2027": "Fija en exactamente 1.500 personas el número máximo de funcionarios a honorarios a suma alzada que podrán pasar a contrata en todo el sector público.",
        "impacto_calle": "Frena drásticamente la regularización laboral en ministerios y servicios. Miles de trabajadores públicos continuarán boleteando a honorarios sin derechos laborales plenos.",
        "icono": "👥"
    },
    {
        "id": "art-24-25-convenios",
        "eje": "Probidad y Transferencias",
        "articulo": "Artículos 24 y 25",
        "titulo": "Blindaje Anti 'Caso Convenios' en Transferencias Privadas",
        "nivel_cambio": "Crítico",
        "tipo_cambio": "Exigencias de Antigüedad y Garantías",
        "norma_2026": "Primer paquete de restricciones a convenios con fundaciones tras la crisis de 2023, con énfasis en concursabilidad y registro SISREC.",
        "norma_2027": "Exige antigüedad mínima de 2 años al postular; boleta de garantía bancaria o póliza por el 100% de anticipos; prohibición total de transferir si directivos tienen parentesco (hasta 3er grado) con autoridades del servicio; y registro de Beneficiarios Finales.",
        "impacto_calle": "Cierra el paso a la creación de fundaciones 'exprés' para adjudicarse fondos de campamentos, cultura o desarrollo social. Las ONG consolidadas deberán inmovilizar capital en garantías bancarias.",
        "icono": "🛡️"
    },
    {
        "id": "art-50-obras",
        "eje": "Infraestructura y Obras Públicas",
        "articulo": "Artículo 50",
        "titulo": "Inicio Material de Obras por Trato Directo sin Espera",
        "nivel_cambio": "Mayor",
        "tipo_cambio": "Agilización Operativa",
        "norma_2026": "Las obras públicas mayores requerían tramitación administrativa completa y control previo de legalidad antes de iniciar faenas en terreno.",
        "norma_2027": "Obras adjudicadas por trato directo hasta 30.000 UTM (~$2.000M) o licitación pública hasta 75.000 UTM (~$5.000M) podrán iniciarse materialmente apenas se notifique la adjudicación, antes de la toma de razón.",
        "impacto_calle": "Acelera el inicio de faenas de pavimentación, muros de contención o APR para reactivación económica, reduciendo el freno burocrático previo de la Contraloría.",
        "icono": "🏗️"
    },
    {
        "id": "art-08-pago-proveedores",
        "eje": "Compras Públicas y PYMES",
        "articulo": "Artículo 8",
        "titulo": "Trazabilidad Electrónica y Pago Oportuno a Proveedores",
        "nivel_cambio": "Moderado",
        "tipo_cambio": "Fiscalización Digital",
        "norma_2026": "Obligación general de pago en 30 días según la Ley 21.131 (Pago Oportuno).",
        "norma_2027": "Incorpora verificación obligatoria contra el Registro Electrónico de Compras y reporte mensual obligatorio de facturas impagas de cada servicio a la DIPRES.",
        "impacto_calle": "Entrega herramientas de transparencia para evitar que servicios públicos y hospitales dilaten pagos a pequeñas empresas y contratistas durante meses.",
        "icono": "💳"
    },
    {
        "id": "art-21-publicidad",
        "eje": "Probidad y Transparencia",
        "articulo": "Artículo 21",
        "titulo": "Prohibición de Promoción Personal con Fondos Públicos",
        "nivel_cambio": "Moderado",
        "tipo_cambio": "Restricción de Propaganda",
        "norma_2026": "Normas generales sobre gastos de difusión y prohibición de publicidad electoral.",
        "norma_2027": "Prohibición taxativa de destinar recursos fiscales de publicidad a piezas o campañas que incluyan la imagen, voz o nombre de autoridades políticas en ejercicio.",
        "impacto_calle": "Evita el uso de presupuestos ministeriales o municipales como plataforma de propaganda personalizada de ministros, alcaldes o parlamentarios.",
        "icono": "🚫"
    },
    {
        "id": "art-41-plataforma",
        "eje": "Transparencia Activa",
        "articulo": "Artículo 41",
        "titulo": "Portal Transaccional Abierto de Hacienda",
        "nivel_cambio": "Mayor",
        "tipo_cambio": "Obligación Tecnológica",
        "norma_2026": "Informes trimestrales y mensuales en PDF o planillas enviados a la Comisión Especial Mixta de Presupuestos.",
        "norma_2027": "Hacienda deberá mantener una plataforma informática pública con ejecución transaccional mensual detallada por región, principales proveedores y receptores de transferencias.",
        "impacto_calle": "Habilita la fiscalización ciudadana y periodística directa al nivel de factura y orden de compra sin tener que esperar informes anuales o solicitudes de Ley de Transparencia.",
        "icono": "💻"
    }
]

def exportar_matriz():
    for d in [DATA_DIR, DIST_DIR / "data", DOCS_DIR / "data"]:
        d.mkdir(parents=True, exist_ok=True)
        out_p = d / "matriz_articulado_2026_2027.json"
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(MATRIZ_ARTICULADO, f, ensure_ascii=False, indent=2)
        print(f"Matriz guardada en {out_p} ({len(MATRIZ_ARTICULADO)} ejes normativos)")

if __name__ == "__main__":
    exportar_matriz()
