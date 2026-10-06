"""
Motor de Traducción Presupuestaria a la Calle (Calle-First Engine).
Convierte asignaciones monetarias abstractas en unidades físicas reconocibles,
costos unitarios observables en compras públicas (ChileCompra) y dilemas éticos de primera línea (Michael Lipsky).
"""

from typing import Dict, Any, Optional

CATALOGO_CALLE = [
    # --- EDUCACIÓN (Partida 09) ---
    {
        "keywords": ["becas", "asistencialidad", "yo elijo mi pc", "notebook"],
        "partidas": ["09"],
        "unidad": "notebooks escolares con internet (Becas TIC / Yo Elijo Mi PC)",
        "icono": "💻",
        "costo_unitario_clp": 330000,
        "organismo": "JUNAEB",
        "contrato_ref": "Licitación Pública Becas TIC (JUNAEB)",
        "dilema": "El colegio debe racionar los equipos o dejar cursos enteros de 7° básico sin computador personal ni conectividad para estudiar."
    },
    {
        "keywords": ["salud escolar", "lentes", "oftalmología"],
        "partidas": ["09"],
        "unidad": "atenciones de salud escolar y lentes ópticos entregados",
        "icono": "👓",
        "costo_unitario_clp": 45000,
        "organismo": "JUNAEB / Salud del Estudiante",
        "contrato_ref": "Programa Servicios Médicos Escolares (JUNAEB)",
        "dilema": "Estudiantes con déficit visual o auditivo esperan meses por un diagnóstico, afectando directamente su aprendizaje en la sala de clases."
    },
    {
        "keywords": ["recursos educativos", "textos", "biblioteca escolar"],
        "partidas": ["09"],
        "unidad": "sets de textos escolares y material didáctico de aula",
        "icono": "📚",
        "costo_unitario_clp": 25000,
        "organismo": "Subsecretaría de Educación",
        "contrato_ref": "Licitación Pública Textos Escolares Mineduc",
        "dilema": "Profesores deben fotocopiar guías o compartir libros entre varios alumnos por falta de textos oficiales del Mineduc."
    },
    {
        "keywords": ["jardines", "junji", "parvular", "sala cuna"],
        "partidas": ["09"],
        "unidad": "cupos anuales de sala cuna y jardín infantil público",
        "icono": "🧸",
        "costo_unitario_clp": 4200000,
        "organismo": "JUNJI / Fundación Integra",
        "contrato_ref": "Subvención de Educación Parvularia y Salas Cuna",
        "dilema": "Madres y padres trabajadores quedan en listas de espera sin opciones de cuidado seguro para sus hijos en la primera infancia."
    },
    {
        "keywords": ["subvenciones a los establecimientos", "subvención escolar"],
        "partidas": ["09"],
        "unidad": "subvenciones anuales base por estudiante matriculado",
        "icono": "🎒",
        "costo_unitario_clp": 1450000,
        "organismo": "Subsecretaría de Educación / Sostenedores",
        "contrato_ref": "Unidad de Subvención Educacional (USE Ley 20.248)",
        "dilema": "Mecanismo inercial obligatorio por ley para sostener salarios de docentes y funcionamiento operativo de escuelas subvencionadas."
    },
    {
        "keywords": ["servicio educativo", "servicio local", "slep", "barrancas", "puerto cordillera", "huasco", "chinchorro", "andalién", "chiloé", "la quebrada", "talagante", "reloncaví"],
        "partidas": ["09"],
        "unidad": "aulas y recintos escolares públicos bajo gestión de SLEP",
        "icono": "🏫",
        "costo_unitario_clp": 380000000,
        "organismo": "Servicios Locales de Educación Pública (SLEP)",
        "contrato_ref": "Sistema de Educación Pública Ley 21.040",
        "dilema": "Traspaso administrativo de escuelas municipales al Estado; no representa holgura en aula sino absorción de nóminas e infraestructura."
    },
    {
        "keywords": ["superior", "gratuidad", "universitaria"],
        "partidas": ["09"],
        "unidad": "aranceles anuales de gratuidad universitaria y técnica",
        "icono": "🎓",
        "costo_unitario_clp": 3800000,
        "organismo": "Subsecretaría de Educación Superior",
        "contrato_ref": "Aportes Institucionales y Gratuidad Ley 21.091",
        "dilema": "Estudiantes vulnerables enfrentan brechas de copago o universidades sufren estrechez financiera en investigación y equipamiento."
    },
    {
        "keywords": ["docente", "profesional docente", "carrera docente"],
        "partidas": ["09"],
        "unidad": "asignaciones de tramo y perfeccionamiento a profesores de aula",
        "icono": "👩‍🏫",
        "costo_unitario_clp": 1800000,
        "organismo": "CPEIP / Mineduc",
        "contrato_ref": "Sistema de Desarrollo Profesional Docente Ley 20.903",
        "dilema": "Docentes ven congeladas o retrasadas sus asignaciones por avance en la carrera profesional."
    },
    {
        "keywords": ["calidad de la educación", "mejoramiento"],
        "partidas": ["09"],
        "unidad": "proyectos de reforzamiento escolar y tutorías en aula",
        "icono": "📝",
        "costo_unitario_clp": 15000000,
        "organismo": "Subsecretaría de Educación",
        "contrato_ref": "Planes de Mejoramiento Educativo (PME)",
        "dilema": "Colegios vulnerables suspenden talleres de lectoescritura y apoyo a alumnos con rezago pedagógico post-pandemia."
    },

    # --- VIVIENDA Y URBANISMO (Partida 18) ---
    {
        "keywords": ["recuperación de barrios", "quiero mi barrio"],
        "partidas": ["18"],
        "unidad": "proyectos integrales de barrio (plazas, sedes y luminarias)",
        "icono": "🏘️",
        "costo_unitario_clp": 350000000,
        "organismo": "MINVU / Municipios",
        "contrato_ref": "Programa Quiero Mi Barrio MINVU",
        "dilema": "Comités barriales quedan con diagnósticos y diseños participativos aprobados pero sin financiamiento para construir las obras prometidas."
    },
    {
        "keywords": ["asentamientos precarios", "campamento"],
        "partidas": ["18"],
        "unidad": "soluciones de agua potable y mitigación de riesgo para familias en campamentos",
        "icono": "💧",
        "costo_unitario_clp": 10000000,
        "organismo": "SERVIU / Asentamientos Precarios",
        "contrato_ref": "Programa de Campamentos MINVU",
        "dilema": "Familias en tomas y campamentos quedan sin acceso a camiones aljibe, grifos de incendio ni obras para evitar derrumbes en invierno."
    },
    {
        "keywords": ["serviu", "subsidio", "vivienda", "tarapacá", "biobío", "coquimbo", "ñuble", "metropolitana", "valparaíso", "araucanía"],
        "partidas": ["18"],
        "unidad": "viviendas sociales definitivas para comités de allegados (DS49)",
        "icono": "🏡",
        "costo_unitario_clp": 45000000,
        "organismo": "SERVIU Regional",
        "contrato_ref": "Fondo Solidario de Elección de Vivienda DS49",
        "dilema": "Comités de vivienda con años de ahorro y terreno calificado deben postergar la licitación de obras, prolongando el hacinamiento."
    },
    {
        "keywords": ["parque metropolitano", "parquemet", "parque"],
        "partidas": ["18"],
        "unidad": "hectáreas de áreas verdes urbanas mantenidas e irrigadas",
        "icono": "🌳",
        "costo_unitario_clp": 12000000,
        "organismo": "Parque Metropolitano de Santiago (Parquemet)",
        "contrato_ref": "Conservación y Mantenimiento Red de Parques Urbanos",
        "dilema": "Parques urbanos en comunas periféricas sufren deterioro de senderos, arborización y sistemas de riego tecnificado."
    },

    # --- SALUD (Partida 16) ---
    {
        "keywords": ["inversion sectorial", "infraestructura", "hospitales", "obras"],
        "partidas": ["16"],
        "unidad": "módulos de reposición y equipamiento mayor en infraestructura hospitalaria",
        "icono": "🏥",
        "costo_unitario_clp": 350000000,
        "organismo": "Subsecretaría de Redes Asistenciales",
        "contrato_ref": "Licitación Obra Pública Hospitalaria Minsal",
        "dilema": "Comunas rurales o periféricas ven paralizada o postergada la construcción y reposición de nuevos hospitales y consultorios."
    },
    {
        "keywords": ["atencion primaria", "consultorio", "cesfam", "aps", "per capita"],
        "partidas": ["16"],
        "unidad": "atenciones integrales de salud en consultorios y CESFAM de barrio",
        "icono": "🩺",
        "costo_unitario_clp": 28000,
        "organismo": "Atención Primaria de Salud (APS) / FONASA",
        "contrato_ref": "Convenio Per Cápita APS Municipal",
        "dilema": "Vecinos deben hacer fila a las 5 AM para conseguir una hora médica o dental en su consultorio municipal."
    },
    {
        "keywords": ["grupo relacionado", "grd", "complejidad", "intervenciones quirurgicas"],
        "partidas": ["16"],
        "unidad": "cirugías mayores y tratamientos hospitalarios de alta complejidad (GRD)",
        "icono": "💉",
        "costo_unitario_clp": 1850000,
        "organismo": "Hospitales Públicos / FONASA GRD",
        "contrato_ref": "Arancel FONASA Modalidad Institucional GRD",
        "dilema": "Pacientes de lista de espera quirúrgica no-GES esperan más de 400 días para operarse de cadera, vesícula o hernias."
    },
    {
        "keywords": ["contingencias", "urgencia", "refuerzo"],
        "partidas": ["16"],
        "unidad": "turnos médicos y refuerzos de personal clínico en urgencias hospitalarias",
        "icono": "🚑",
        "costo_unitario_clp": 250000,
        "organismo": "Servicios de Salud / Redes Asistenciales",
        "contrato_ref": "Refuerzo Clínico Campaña de Invierno / Contingencias",
        "dilema": "Servicios de urgencia hospitalaria colapsan con pacientes en camillas de pasillo por falta de personal médico de reemplazo."
    },
    {
        "keywords": ["cenabast", "abastecimiento", "farmacos", "medicamentos"],
        "partidas": ["16"],
        "unidad": "canastas de medicamentos e insumos críticos distribuidos a la red pública",
        "icono": "💊",
        "costo_unitario_clp": 35000,
        "organismo": "Central de Abastecimiento (CENABAST)",
        "contrato_ref": "Licitación Centralizada Fármacos CENABAST",
        "dilema": "Farmacias de hospitales y CESFAM quiebran stock de remedios crónicos para diabetes e hipertensión."
    },
    {
        "keywords": ["red publica de salud", "servicio de salud", "hospital", "salud publica", "fondo nacional"],
        "partidas": ["16"],
        "unidad": "consultas médicas de especialista y procedimientos diagnósticos hospitalarios",
        "icono": "🩺",
        "costo_unitario_clp": 65000,
        "organismo": "Servicio de Salud Regional / Hospital Base",
        "contrato_ref": "Prestaciones Hospitalarias Especializadas",
        "dilema": "Pacientes derivados desde consultorios esperan meses por una interconsulta con cardiólogo, neurólogo u oftalmólogo."
    },

    # --- CULTURAS (Partida 29) ---
    {
        "keywords": ["fomento", "organizaciones", "cultural", "talleres"],
        "partidas": ["29"],
        "unidad": "talleres artísticos barriales y ciclos comunitarios",
        "icono": "🎭",
        "costo_unitario_clp": 1500000,
        "organismo": "Subsecretaría de las Culturas / Centros Culturales",
        "contrato_ref": "Mercado Público OC 4412-45-CM25 Culturas",
        "dilema": "Agrupaciones artísticas locales y centros comunitarios quedan sin financiamiento para talleres juveniles de prevención psicosocial."
    },
    {
        "keywords": ["fondos", "fondart", "fomento del libro", "audiovisual"],
        "partidas": ["29"],
        "unidad": "proyectos artísticos y culturales concursables adjudicados",
        "icono": "🎨",
        "costo_unitario_clp": 15000000,
        "organismo": "Fondos de Fomento Cultural (FONDART)",
        "contrato_ref": "Fondos Concursables FONDART / Música / Audiovisual",
        "dilema": "Compañías de teatro emergentes, cineastas y creadores de regiones ven recortados los cupos de fondos concursables del Estado."
    },
    {
        "keywords": ["biblioteca", "libros"],
        "partidas": ["29"],
        "unidad": "adquisición de colecciones y equipamiento para bibliotecas públicas",
        "icono": "📖",
        "costo_unitario_clp": 5000000,
        "organismo": "Servicio Nacional del Patrimonio Cultural",
        "contrato_ref": "Red Nacional de Bibliotecas Públicas",
        "dilema": "Bibliotecas municipales y comunitarias quedan sin presupuesto para renovar títulos, computadores de acceso libre y talleres infantiles."
    },
    {
        "keywords": ["museos", "patrimonio", "monumentos"],
        "partidas": ["29"],
        "unidad": "conservación de sitios patrimoniales y exposiciones abiertas",
        "icono": "🏛️",
        "costo_unitario_clp": 25000000,
        "organismo": "Servicio Nacional del Patrimonio / Monumentos Nacionales",
        "contrato_ref": "Fondo del Patrimonio Cultural",
        "dilema": "Museos regionales deben reducir horarios de atención gratuita y suspender obras de restauración en monumentos históricos en riesgo."
    },

    # --- GOBIERNOS REGIONALES (Partida 31) ---
    {
        "keywords": ["gobierno regional", "gore", "fril", "inversión regional", "asociatividad", "planes especiales"],
        "partidas": ["31"],
        "unidad": "proyectos comunales FRIL (luminarias LED, veredas y sedes comunitarias)",
        "icono": "💡",
        "costo_unitario_clp": 125000000,
        "organismo": "Gobiernos Regionales / Municipalidades Rurales",
        "contrato_ref": "Mercado Público OC 2456-112-LR24 GORE",
        "dilema": "Alcaldes de comunas rurales quedan sin financiamiento rápido para pavimentar pasajes de tierra, arreglar alumbrado vecinal o postas."
    },

    # --- INTERIOR Y SEGURIDAD (Partida 05) ---
    {
        "keywords": ["bomberos"],
        "partidas": ["05"],
        "unidad": "carros bomba o equipamiento de protección para compañías de bomberos",
        "icono": "🚒",
        "costo_unitario_clp": 250000000,
        "organismo": "Junta Nacional de Cuerpos de Bomberos",
        "contrato_ref": "Subvención Estatal a Bomberos de Chile",
        "dilema": "Cuerpos de bomberos voluntarios deben realizar colectas callejeras para costear combustible de carros y trajes normados contra fuego."
    },
    {
        "keywords": ["desarrollo regional", "subdere", "desarrollo local", "comunal"],
        "partidas": ["05"],
        "unidad": "proyectos de Mejoramiento Urbano y Barrial (PMU Subdere)",
        "icono": "🚧",
        "costo_unitario_clp": 75000000,
        "organismo": "SUBDERE / Municipios",
        "contrato_ref": "Programa de Mejoramiento Urbano (PMU)",
        "dilema": "Comunas de menores recursos ven paralizados proyectos de emergencia para alcantarillado, plazas y recuperación de sitios eriazos."
    },
    {
        "keywords": ["seguridad", "interior", "policial", "carabineros", "gobierno interior"],
        "partidas": ["05"],
        "unidad": "vehículos radiopatrulla policial equipados para vigilancia barrial",
        "icono": "🚓",
        "costo_unitario_clp": 45000000,
        "organismo": "Subsecretaría del Interior / Carabineros",
        "contrato_ref": "Licitación Parque Vehicular Carabineros de Chile",
        "dilema": "Comisarías y retenes de comunas con alta delincuencia operan con móviles dados de baja o reducen los turnos de patrullaje preventivo."
    }
]

def calcular_bajada_calle(programa: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Calcula la equivalencia tangible en la calle para un programa presupuestario."""
    import unicodedata
    nom_prog = (programa.get("nombre_programa") or "").lower()
    nom_cap = (programa.get("nombre_capitulo") or "").lower()
    cod = str(programa.get("codigo") or "")
    partida = str(programa.get("partida") or (cod.split("-")[0] if "-" in cod else "")).zfill(2)
    texto_busca = f"{nom_prog} {nom_cap}"
    texto_busca = "".join(c for c in unicodedata.normalize("NFKD", texto_busca) if not unicodedata.combining(c))
    
    # 1. Búsqueda de alta especificidad (partida + keywords)
    regla_elegida = None
    for r in CATALOGO_CALLE:
        if partida in r["partidas"]:
            for k in r["keywords"]:
                k_norm = "".join(c for c in unicodedata.normalize("NFKD", k.lower()) if not unicodedata.combining(c))
                if k_norm in texto_busca:
                    regla_elegida = r
                    break
            if regla_elegida:
                break
            
    # 2. Regla fallback por partida si no calzó ninguna keyword específica
    if not regla_elegida:
        for r in CATALOGO_CALLE:
            if partida in r["partidas"]:
                regla_elegida = r
                break
                
    if not regla_elegida:
        return None
        
    dif_mclp = programa.get("dif_vs_ini_mclp") or programa.get("dif_vs_vig_mclp") or 0
    monto_clp = abs(dif_mclp) * 1000 # Convertir de Miles de Pesos (M$) de la ley a Pesos (CLP)
    costo_u = regla_elegida["costo_unitario_clp"]
    cantidad = int(round(monto_clp / costo_u))
    
    if cantidad == 0:
        return None
        
    signo = "-" if dif_mclp < 0 else "+"
    verbo = "menos" if dif_mclp < 0 else "adicionales"
    
    # Formatear número con puntos de miles
    cant_str = f"{cantidad:,}".replace(",", ".")
    impacto_texto = f"{signo}{cant_str} {regla_elegida['unidad']} {verbo}"
    
    return {
        "icono": regla_elegida["icono"],
        "unidad": regla_elegida["unidad"],
        "costo_unitario_clp": costo_u,
        "cantidad": cantidad,
        "signo": signo,
        "impacto_texto": impacto_texto,
        "organismo": regla_elegida["organismo"],
        "contrato_ref": regla_elegida["contrato_ref"],
        "dilema": regla_elegida["dilema"]
    }


estimar_bajada_calle = calcular_bajada_calle
