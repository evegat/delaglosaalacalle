import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import json

xml_path = Path("data/proyecto_presupuesto_2027_dipres_oficial.xml")
tree = ET.parse(xml_path)
root = tree.getroot()

# Namespaces
ns = {"pi": "http://www.contraloria.cl/Informes/SP/PresupuestoInicial"}

programas_2027 = []
partidas_dict = {}
capitulos_dict = {}

for ley in root.findall("pi:LeyDePresupuesto", ns):
    p_cod = ley.findtext("pi:codigoPartida", default="", namespaces=ns).strip().zfill(2)
    p_nom = ley.findtext("pi:nombrePartida", default="", namespaces=ns).strip()
    c_cod = ley.findtext("pi:codigoCapitulo", default="", namespaces=ns).strip().zfill(2)
    c_nom = ley.findtext("pi:nombreCapitulo", default="", namespaces=ns).strip()
    pr_cod = ley.findtext("pi:codigoPrograma", default="", namespaces=ns).strip().zfill(2)
    pr_nom = ley.findtext("pi:nombrePrograma", default="", namespaces=ns).strip()
    
    code = f"{p_cod}-{c_cod}-{pr_cod}"
    
    partidas_dict[p_cod] = p_nom
    capitulos_dict[f"{p_cod}-{c_cod}"] = c_nom
    
    cuentas = ley.find("pi:CuentasPresupuestos", ns)
    tot_gastos_clp = int(cuentas.findtext("pi:totalGastosCLP", default="0", namespaces=ns).strip())
    tot_gastos_usd = int(cuentas.findtext("pi:totalGastosUSD", default="0", namespaces=ns).strip())
    tot_ingresos_clp = int(cuentas.findtext("pi:totalIngresosCLP", default="0", namespaces=ns).strip())
    tot_ingresos_usd = int(cuentas.findtext("pi:totalIngresosUSD", default="0", namespaces=ns).strip())
    
    # Subtítulos de gastos (21 a 35)
    gastos_por_subtitulo = defaultdict(int)
    for c in cuentas.findall("pi:Cuenta", ns):
        tipo_cuenta = c.get("tipoCuenta")
        if tipo_cuenta == "G": # Gasto
            sub = c.findtext("pi:subtitulo", default="", namespaces=ns).strip()
            item = c.findtext("pi:item", default="", namespaces=ns).strip()
            asig = c.findtext("pi:asignacion", default="", namespaces=ns).strip()
            # Nivel subtitulo directo
            if item == "00" and asig == "000":
                monto = int(c.findtext("pi:montoCLP", default="0", namespaces=ns).strip())
                gastos_por_subtitulo[sub] += monto

    programas_2027.append({
        "codigo": code,
        "partida": p_cod,
        "capitulo": c_cod,
        "programa": pr_cod,
        "nombre_partida": p_nom,
        "nombre_capitulo": c_nom,
        "nombre_programa": pr_nom,
        "proy_2027_mclp": tot_gastos_clp,
        "proy_2027_usd": tot_gastos_usd,
        "tot_ingresos_clp": tot_ingresos_clp,
        "tot_ingresos_usd": tot_ingresos_usd,
        "gastos_subtitulos": dict(gastos_por_subtitulo)
    })

print(f"Total programas extraídos de XML: {len(programas_2027)}")
print(f"Partidas únicas: {len(partidas_dict)}")
for p, nom in sorted(partidas_dict.items()):
    print(f"  {p}: {nom}")

# Guardar catálogo canónico 2027
out_path = Path("data/catalogo_programas_2027_dipres.json")
out_path.write_text(json.dumps(programas_2027, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Guardado catálogo en {out_path} ({len(programas_2027)} programas)")
