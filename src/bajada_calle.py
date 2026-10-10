"""
Motor de Traducción Presupuestaria a la Calle (Calle-First Engine).
Convierte asignaciones monetarias abstractas en unidades físicas reconocibles,
costos unitarios observables en compras públicas (ChileCompra) y dilemas éticos de primera línea (Michael Lipsky).
"""

from typing import Dict, Any, Optional

CATALOGO_CALLE = [
    # --- EDUCACIÓN (Partida 09) ---
    {
        "keywords": ["becas", "asistencialidad", "yo elijo mi pc", "notebook", "computador", "computadores", "tic", "laptop"],
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
        "keywords": ["servicio educativo", "servicio local", "slep", "gastos administrativos", "barrancas", "puerto cordillera", "huasco", "chinchorro", "andalién", "chiloé", "la quebrada", "talagante", "reloncaví", "costa araucanía", "gabriela mistral", "valparaíso", "colchagua", "llanquihue", "iquique", "atacama", "magallanes", "punche", "licancabur", "maipo", "valdivia", "chiloé"],
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
        "keywords": ["calidad de la educación", "mejoramiento", "educacion", "educación", "subsecretaría", "superintendencia", "direccion", "publica", "escolar"],
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
        "keywords": ["red publica de salud", "servicio de salud", "hospital", "salud publica", "fondo nacional", "redes asistenciales", "salud", "atencion", "asistencial"],
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
    },

    # --- SEGURIDAD PÚBLICA (Partida 32) ---
    {
        "keywords": ["crimen organizado", "investigaciones", "policia", "pdi"],
        "partidas": ["32"],
        "unidad": "kits tecnológicos y periciales contra el crimen organizado",
        "icono": "🛡️",
        "costo_unitario_clp": 85000000,
        "organismo": "Policía de Investigaciones / Subsecretaría de Seguridad",
        "contrato_ref": "Plan Nacional Contra el Crimen Organizado Ley 21.577",
        "dilema": "Unidades policiales especializadas ven limitada la interceptación y peritaje balístico frente a bandas delictuales transnacionales."
    },
    {
        "keywords": ["carabineros", "patrullaje", "seguridad rural", "rural"],
        "partidas": ["32", "05"],
        "unidad": "vehículos radiopatrulla 4x4 equipados para seguridad barrial y rural",
        "icono": "🚓",
        "costo_unitario_clp": 52000000,
        "organismo": "Carabineros de Chile / Subsecretaría de Seguridad",
        "contrato_ref": "Licitación Parque Vehicular Blindado y Táctico Carabineros",
        "dilema": "Retenes de zonas rurales y comisarías de barrios periféricos reducen cuadrantes de patrullaje preventivo nocturno."
    },
    {
        "keywords": ["lazos", "prevencion", "denuncia seguro", "comunitaria"],
        "partidas": ["32", "05"],
        "unidad": "intervenciones psicosociales familiares del Programa Lazos",
        "icono": "🤝",
        "costo_unitario_clp": 2400000,
        "organismo": "Subsecretaría de Prevención del Delito / Seguridad Pública",
        "contrato_ref": "Programa Lazos - Terapia Multisistémica",
        "dilema": "Jóvenes en riesgo inicial de deserción escolar y delincuencia quedan sin acompañamiento terapéutico intensivo en su hogar."
    },

    # --- OBRAS PÚBLICAS (Partida 12) ---
    {
        "keywords": ["agua potable", "apr", "hidraulicas", "rural"],
        "partidas": ["12"],
        "unidad": "arranques y conexiones de Agua Potable Rural (APR) domiciliarias",
        "icono": "🚰",
        "costo_unitario_clp": 8500000,
        "organismo": "Dirección de Obras Hidráulicas (DOH / MOP)",
        "contrato_ref": "Licitación Pública Sistemas APR Dirección Obras Hidráulicas",
        "dilema": "Comunidades rurales deben seguir abasteciéndose con camiones aljibe por retrasos en pozos y matrices de agua potable."
    },
    {
        "keywords": ["vialidad", "caminos", "pavimento", "puentes", "carreteras", "concesiones", "aeropuertos", "obras"],
        "partidas": ["12"],
        "unidad": "kilómetros de conservación de caminos básicos y carpetas asfálticas",
        "icono": "🛣️",
        "costo_unitario_clp": 120000000,
        "organismo": "Dirección de Vialidad (MOP)",
        "contrato_ref": "Conservación Global de Caminos Dirección de Vialidad MOP",
        "dilema": "Localidades aisladas sufren cortes de conectividad invernal y baches profundos en rutas productivas."
    },

    # --- JUSTICIA Y DERECHOS HUMANOS (Partida 10) ---
    {
        "keywords": ["gendarmeria", "penitenciario", "carceles", "custodia"],
        "partidas": ["10"],
        "unidad": "plazas de custodia y control penitenciario seguro en recintos penales",
        "icono": "🏢",
        "costo_unitario_clp": 18000000,
        "organismo": "Gendarmería de Chile",
        "contrato_ref": "Gestión y Equipamiento Penitenciario Gendarmería",
        "dilema": "Hacinamiento en módulos carcelarios sobrepasa capacidades de seguridad y programas de reinserción laboral."
    },
    {
        "keywords": ["registro civil", "identificacion", "cedula", "pasaporte", "defensoria", "judicial"],
        "partidas": ["10"],
        "unidad": "operativos móviles en terreno del Registro Civil e Identificación",
        "icono": "🆔",
        "costo_unitario_clp": 12000000,
        "organismo": "Servicio de Registro Civil e Identificación",
        "contrato_ref": "Convenio de Operativos Terreno y Atención Ciudadana",
        "dilema": "Adultos mayores y zonas rurales quedan sin acceso expedito a renovación de carnet de identidad y certificados."
    },

    # --- TRABAJO Y PREVISIÓN SOCIAL (Partida 15) ---
    {
        "keywords": ["capacitacion", "sence", "empleo", "proempleo", "oficios", "reconversión"],
        "partidas": ["15"],
        "unidad": "becas de capacitación laboral técnica y reconversión de oficios (SENCE)",
        "icono": "🛠️",
        "costo_unitario_clp": 1250000,
        "organismo": "Servicio Nacional de Capacitación y Empleo (SENCE)",
        "contrato_ref": "Licitación Bonos y Cursos Capacitación SENCE",
        "dilema": "Trabajadores desempleados quedan sin habilidades formativas para reintegrarse al mercado formal."
    },
    {
        "keywords": ["trabajo", "inspeccion", "fiscalizacion laboral", "direccion del trabajo"],
        "partidas": ["15"],
        "unidad": "fiscalizaciones laborales inspectivas en faenas y empresas",
        "icono": "📋",
        "costo_unitario_clp": 380000,
        "organismo": "Dirección del Trabajo (DT)",
        "contrato_ref": "Programa de Fiscalización Laboral en Terreno DT",
        "dilema": "Denuncias por abusos laborales, no pago de cotizaciones o informalidad quedan sin inspectores disponibles."
    },
    {
        "keywords": ["prevision", "social", "pensiones", "credito prendario", "dicrep", "tia rica", "ips"],
        "partidas": ["15"],
        "unidad": "atenciones y tramitaciones de pensiones y seguridad social (IPS / DICREP)",
        "icono": "🪙",
        "costo_unitario_clp": 45000,
        "organismo": "Instituto de Previsión Social (IPS)",
        "contrato_ref": "Plataforma Integral de Atención Previsional ChileAtiende",
        "dilema": "Pensionados y familias vulnerables deben hacer largas filas o esperar meses por resoluciones de beneficios."
    },

    # --- AGRICULTURA (Partida 13) ---
    {
        "keywords": ["indap", "campesino", "agricultura familiar", "pequeño productor", "riego"],
        "partidas": ["13"],
        "unidad": "créditos y subsidios de fomento productivo para familias campesinas (INDAP)",
        "icono": "🌾",
        "costo_unitario_clp": 3500000,
        "organismo": "Instituto de Desarrollo Agropecuario (INDAP)",
        "contrato_ref": "Programa de Asistencia Financiera y Riego INDAP",
        "dilema": "Pequeños agricultores pierden cosechas frente a sequías por falta de tecnificación de riego y fertilizantes."
    },
    {
        "keywords": ["sag", "agricola y ganadero", "inspecciones", "barreras", "sanitario"],
        "partidas": ["13"],
        "unidad": "inspecciones zoofitosanitarias y controles fronterizos SAG",
        "icono": "🍎",
        "costo_unitario_clp": 280000,
        "organismo": "Servicio Agrícola y Ganadero (SAG)",
        "contrato_ref": "Fiscalización Sanitaria de Fronteras y Predios SAG",
        "dilema": "Riesgo de ingreso de plagas cuarentenarias como la mosca de la fruta que paralizan exportaciones agrícolas."
    },
    {
        "keywords": ["conaf", "forestal", "incendios", "brigadas", "bosques", "areas silvestres"],
        "partidas": ["13"],
        "unidad": "horas de operación de brigadas forestales y cortafuegos preventivos (CONAF)",
        "icono": "🚒",
        "costo_unitario_clp": 1850000,
        "organismo": "Corporación Nacional Forestal (CONAF)",
        "contrato_ref": "Operativo Combate y Prevención de Incendios Forestales CONAF",
        "dilema": "Demoras en despliegue ante siniestros forestales aumentan el riesgo de propagación hacia zonas pobladas."
    },

    # --- TRANSPORTES Y TELECOMUNICACIONES (Partida 19) ---
    {
        "keywords": ["subsidio", "transporte publico", "pasaje", "red movilidad", "tarifa"],
        "partidas": ["19"],
        "unidad": "pasajes de transporte público subsidiados para estudiantes y adultos mayores",
        "icono": "🚌",
        "costo_unitario_clp": 750,
        "organismo": "Directorio de Transporte Público Metropolitano (DTPM) / MTT Regional",
        "contrato_ref": "Subsidio Nacional al Transporte Público Ley 20.378",
        "dilema": "Alza directa de la tarifa del pasaje que golpea el presupuesto mensual de las familias trabajadoras."
    },
    {
        "keywords": ["transito", "fiscalizacion", "camaras", "infracciones", "telecomunicaciones", "subtel", "fibra"],
        "partidas": ["19"],
        "unidad": "puntos de fiscalización técnica y control de tránsito automatizado",
        "icono": "🚦",
        "costo_unitario_clp": 4500000,
        "organismo": "División de Fiscalización MTT / Subtel",
        "contrato_ref": "Red de Sensores y Fiscalización Automatizada MTT",
        "dilema": "Aumento de siniestros viales y buses piratas sin revisión técnica en rutas interurbanas."
    },

    # --- DESARROLLO SOCIAL Y FAMILIA (Partida 21) ---
    {
        "keywords": ["cuidados", "chile cuida", "cuidadores", "discapacidad", "dependencia"],
        "partidas": ["21"],
        "unidad": "subsidios mensuales y atenciones domiciliarias de la Red Chile Cuida",
        "icono": "🧑‍🦽",
        "costo_unitario_clp": 320000,
        "organismo": "Subsecretaría de Servicios Sociales / Chile Cuida",
        "contrato_ref": "Sistema Nacional de Apoyos y Cuidados Ley 21.650",
        "dilema": "Mujeres cuidadoras continúan en aislamiento económico sin relevos ni transferencias para medicamentos."
    },
    {
        "keywords": ["solidaridad", "fosis", "ingresos autonomos", "pobreza", "seguridades", "oportunidades", "calle"],
        "partidas": ["21"],
        "unidad": "emprendimientos familiares y planes de apoyo socioeconómico (FOSIS)",
        "icono": "🌱",
        "costo_unitario_clp": 1600000,
        "organismo": "Fondo de Solidaridad e Inversión Social (FOSIS)",
        "contrato_ref": "Programa Emprendamos y Seguridad y Oportunidades FOSIS",
        "dilema": "Hogares bajo la línea de pobreza extrema quedan sin capital semilla para salir de la vulnerabilidad."
    },

    # --- MEDIO AMBIENTE (Partida 25) ---
    {
        "keywords": ["evaluacion ambiental", "sea", "superintendencia", "sma", "fiscalizacion", "biodiversidad", "areas protegidas"],
        "partidas": ["25"],
        "unidad": "fiscalizaciones ambientales en terreno de normas de emisión y RCA",
        "icono": "🌳",
        "costo_unitario_clp": 2200000,
        "organismo": "Superintendencia del Medio Ambiente (SMA) / SEA",
        "contrato_ref": "Planes de Fiscalización y Monitoreo Ambiental SMA",
        "dilema": "Vecinos de zonas saturadas sufren episodios críticos de contaminación sin inspectores para sancionar a las fuentes."
    },

    # --- ECONOMÍA, FOMENTO Y TURISMO (Partida 07) ---
    {
        "keywords": ["corfo", "sercotec", "pymes", "innovacion", "emprendimiento", "turismo", "sernatur", "pesca", "sernapesca"],
        "partidas": ["07"],
        "unidad": "subsidios de reactivación y digitalización para micro y pequeñas empresas (Sercotec/Corfo)",
        "icono": "🏪",
        "costo_unitario_clp": 4500000,
        "organismo": "SERCOTEC / CORFO",
        "contrato_ref": "Fondos Concursables Capital Abeja y Capital Semilla SERCOTEC",
        "dilema": "Locatarios de barrio y microempresas turísticas deben cerrar por falta de financiamiento productivo."
    },

    # --- VIVIENDA Y URBANISMO (Partida 18) ---
    {
        "keywords": ["vivienda", "subsidio habitacional", "campamentos", "serviu", "barrios", "pavimentos"],
        "partidas": ["18"],
        "unidad": "subsidios habitacionales DS49 para soluciones habitacionales definitivas",
        "icono": "🏠",
        "costo_unitario_clp": 38000000,
        "organismo": "SERVIU / Ministerio de Vivienda y Urbanismo",
        "contrato_ref": "Plan de Emergencia Habitacional Ley 21.450",
        "dilema": "Familias en comités de allegados o campamentos prolongan su espera en condiciones de hacinamiento."
    },

    # --- HACIENDA (Partida 08) ---
    {
        "keywords": ["sii", "impuestos internos", "tributario", "fiscalizacion tributaria", "tesoreria", "tgr", "aduanas", "chilecompra", "compras publicas", "modernizacion", "hacienda", "secretaria", "administracion general"],
        "partidas": ["08"],
        "unidad": "auditorías tributarias y fiscalizaciones aduaneras automatizadas",
        "icono": "📊",
        "costo_unitario_clp": 1250000,
        "organismo": "Servicio de Impuestos Internos (SII) / TGR / Aduanas",
        "contrato_ref": "Plan de Fiscalización y Modernización Tecnológica SII",
        "dilema": "Evasión y elusión fiscal quedan sin peritaje ante falta de auditores informáticos especializados."
    },

    # --- DEFENSA NACIONAL (Partida 11) ---
    {
        "keywords": ["ejército", "ejercito", "armada", "fuerza aérea", "fuerza aerea", "defensa", "militar", "fronteras", "salud militar"],
        "partidas": ["11"],
        "unidad": "operativos de resguardo y patrullaje de fronteras terrestres y marítimas",
        "icono": "🛡️",
        "costo_unitario_clp": 8500000,
        "organismo": "Fuerzas Armadas de Chile / Estado Mayor Conjunto",
        "contrato_ref": "Despliegue Operativo Control Fronterizo Ley 21.542",
        "dilema": "Pasos no habilitados en el norte quedan desguarnecidos por falta de combustible y equipamiento térmico."
    },

    # --- DESARROLLO SOCIAL AMPLIADO (Partida 21) ---
    {
        "keywords": ["adulto mayor", "senama", "eleam", "indigena", "conadi", "juventud", "injuv", "servicios sociales", "sociales"],
        "partidas": ["21"],
        "unidad": "cupos en residencias protegidas para adultos mayores y fondos comunitarios (SENAMA/CONADI)",
        "icono": "👵",
        "costo_unitario_clp": 950000,
        "organismo": "SENAMA / CONADI / Subsecretaría de Servicios Sociales",
        "contrato_ref": "Red de Establecimientos de Larga Estadía para Adultos Mayores (ELEAM)",
        "dilema": "Personas mayores en abandono quedan sin cuidados residenciales básicos ni medicamentos."
    },

    # --- ECONOMÍA AMPLIADA (Partida 07) ---
    {
        "keywords": ["consumidor", "sernac", "economia", "economía", "empresas de menor tamaño", "inversión", "sectoriales"],
        "partidas": ["07"],
        "unidad": "mediaciones y fiscalizaciones colectivas de derechos del consumidor (SERNAC)",
        "icono": "🛒",
        "costo_unitario_clp": 180000,
        "organismo": "Servicio Nacional del Consumidor (SERNAC)",
        "contrato_ref": "Programa de Fiscalización y Protección al Consumidor SERNAC",
        "dilema": "Reclamos ciudadanos por cobros indebidos de servicios básicos o retail quedan sin mediación efectiva."
    }
]

def calcular_bajada_calle(programa: Dict[str, Any], base: str = 'inicial') -> Optional[Dict[str, Any]]:
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
            
    if not regla_elegida:
        return None
        
    if base not in ('inicial', 'vigente'):
        raise ValueError('Base de comparación inválida')
    dif_mclp = programa.get('dif_vs_ini_mclp' if base == 'inicial' else 'dif_vs_vig_mclp')
    if dif_mclp is None or dif_mclp == 0:
        return None
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
        'base_comparacion': base,
        'tipo_asociacion': 'coincidencia_textual_no_adjudicacion_verificada',
        'estado_costo': 'referencia_no_verificada',
        'limite_metodologico': 'Escenario con costo de referencia no verificado; no demuestra prestaciones efectivamente perdidas o ganadas.',
        "icono": regla_elegida["icono"],
        "unidad": regla_elegida["unidad"],
        "costo_unitario_clp": costo_u,
        "cantidad": cantidad,
        "signo": signo,
        "impacto_texto": impacto_texto,
        "organismo": regla_elegida["organismo"],
        "contrato_ref": regla_elegida["contrato_ref"],
        "dilema": 'Hipótesis por verificar: ' + regla_elegida["dilema"]
    }


estimar_bajada_calle = calcular_bajada_calle
