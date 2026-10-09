
'use strict';
const $=id=>document.getElementById(id);
function elemento(tag,text,clase){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(clase)e.className=clase;return e;}

// Capa de datos isomórfica: API FastAPI en local + Fallback estático en GitHub Pages / CDN
const _cacheEstatico = {
  presupuesto2027: null,
  programas: null,
  servicios: null,
  comparacion: null,
  equivalencias: null,
  recorridos: null,
  articulado: null
};

const CIVIC_ALIASES = {
  "slep": ["servicio local", "educacion publica", "valle diguillin", "barrancas", "puerto cordillera", "chinchorro", "andalien", "costa araucania", "huasco", "atacama", "chiloe", "magallanes", "llanquihue", "colchagua", "valparaiso", "san antonio", "iquique", "antofagasta"],
  "escuela": ["servicio local", "slep", "educacion publica", "establecimientos", "subvenciones"],
  "colegio": ["servicio local", "slep", "educacion publica", "establecimientos", "subvenciones"],
  "calidad": ["calidad de la educacion", "mejoramiento", "desarrollo profesional docente"],
  "computador": ["becas y asistencialidad", "yo elijo mi pc", "notebook", "tecnologias"],
  "pc": ["becas y asistencialidad", "yo elijo mi pc", "notebook"],
  "notebook": ["becas y asistencialidad", "yo elijo mi pc"],
  "hospital": ["inversion sectorial", "infraestructura", "redes asistenciales", "servicio de salud"],
  "medico": ["redes asistenciales", "atencion primaria", "consultas", "especialidades"],
  "fonasa": ["fondo nacional de salud", "atencion primaria", "prestaciones"],
  "campamento": ["asentamientos precarios", "campamentos"],
  "plaza": ["recuperacion de barrios", "quiero mi barrio"],
  "barrio": ["recuperacion de barrios", "quiero mi barrio", "mejoramiento urbano"],
  "seguridad": ["seguridad publica", "carabineros", "policia", "orden publico", "crimen organizado", "lazos", "denuncia seguro"],
  "mujer": ["mujer", "sernameg", "violencia", "femicidio", "equidad de genero"],
  "genero": ["mujer", "sernameg", "violencia", "femicidio", "equidad de genero"],
  "sernameg": ["servicio nacional de la mujer", "sernameg", "mujer", "violencia", "femicidio"],
  "femicidio": ["violencia", "sernameg", "mujer", "femicidio"]
};

const STOPWORDS = new Set([
  'de', 'la', 'el', 'en', 'y', 'los', 'del', 'las', 'un', 'una', 'por', 'con', 'para', 'que', 'al', 'o', 'su', 'se', 'lo',
  'como', 'mas', 'pero', 'sus', 'le', 'ya', 'ha', 'este', 'esta', 'parte', 'partes', 'programa', 'programas',
  'rebaja', 'rebajas', 'rebajaron', 'recorte', 'recortes', 'recortaron', 'baja', 'bajas', 'disminucion', 'aumento', 'aumentos', 'subida', 'subieron'
]);

const ORGANISMOS_SIGLAS = {
  "junta nacional de auxilio escolar y becas": "junaeb",
  "junta nacional de jardines infantiles": "junji",
  "fondo nacional de salud": "fonasa",
  "servicio nacional de la mujer": "sernameg",
  "servicio nacional de menores": "sename",
  "servicio nacional del adulto mayor": "senama",
  "servicio nacional de la discapacidad": "senadis",
  "direccion general de aeronautica civil": "dgac",
  "subsecretaria de desarrollo regional": "subdere",
  "instituto nacional de estadisticas": "ine",
  "instituto nacional de deportes": "ind"
};

function normalizarTexto(txt) {
  return (txt || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
}

function coincidePrograma(p, q) {
  const rawTokens = normalizarTexto(q).split(/\s+/).filter(t => t.length >= 2);
  const tokens = rawTokens.filter(t => !STOPWORDS.has(t));
  const tokensFinales = tokens.length ? tokens : rawTokens;
  if (!tokensFinales.length) return true;

  const partes = [p.codigo, p.nombre_partida, p.nombre_capitulo, p.nombre_programa];
  if (p.bajada_calle) {
    partes.push(p.bajada_calle.impacto_texto, p.bajada_calle.unidad, p.bajada_calle.dilema, p.bajada_calle.contrato_ref);
  }
  let texto = normalizarTexto(partes.join(' '));

  for (const [org, sigla] of Object.entries(ORGANISMOS_SIGLAS)) {
    if (texto.includes(org)) texto += ' ' + sigla;
  }

  if (texto.includes('servicio local')) texto += ' slep sleps escuela escuelas colegios educacion publica';
  if (texto.includes('recuperacion de barrios') || texto.includes('quiero mi barrio')) texto += ' quiero mi barrio barrio barrios plazas luminarias';
  if (texto.includes('asentamientos precarios') || texto.includes('campamentos')) texto += ' campamento campamentos tomas agua potable';
  if (texto.includes('becas y asistencialidad') || texto.includes('junaeb')) {
    texto += ' yo elijo mi pc becas tic computador computadores computacion pc pcs notebook notebooks escolares laptops conectividad tecnologia septimo basico';
  }
  if (String(p.partida || '').padStart(2, '0') === '16') texto += ' salud hospital hospitales cesfam consultorio consultorios camas urgencia cirugia cirugias medico medicos';
  if (String(p.partida || '').padStart(2, '0') === '27') texto += ' mujer mujeres genero sernameg violencia femicidio femicidios equidad de genero ministerio de la mujer igualdad de genero prevencion atencion';

  return tokensFinales.every(t => {
    if (t.length <= 3) {
      const re = new RegExp('\\b' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(s)?\\b');
      return re.test(texto);
    }
    return texto.includes(t);
  });
}

async function cargarJSONEstatico(nombre) {
  const r = await fetch('data/' + nombre, { headers: { Accept: 'application/json' } });
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}

function resumenPresupuesto(progs) {
  const disponible = v => typeof v === 'number' && Number.isFinite(v);
  const total = (campo, rows) => {
    const valores = rows.map(p => p[campo]).filter(disponible);
    return valores.length ? valores.reduce((a, b) => a + b, 0) : null;
  };
  const comparables = {};
  for (const [nombre, campo] of [['inicial', 'ini_2026_mclp'], ['vigente', 'vig_2026_mclp']]) {
    const pares = progs.filter(p => disponible(p[campo]) && disponible(p.proy_2027_mclp));
    const base = total(campo, pares), proyecto = total('proy_2027_mclp', pares);
    comparables[nombre] = {total_programas: pares.length, base_2026_mclp: base,
      proyecto_2027_mclp: proyecto, diferencia_mclp: base === null ? null : proyecto - base,
      variacion_pct: base > 0 ? Math.round((proyecto / base - 1) * 10000) / 100 : null};
  }
  return {metodo: 'M$ nominales; diferencias sobre los mismos códigos con ambos valores disponibles. Códigos iguales no prueban perímetros institucionales equivalentes. Suma de programas, no gasto público consolidado. No demuestra prestaciones perdidas.',
    totales_mclp: {inicial_2026: total('ini_2026_mclp', progs), vigente_2026: total('vig_2026_mclp', progs),
    proyecto_2027: total('proy_2027_mclp', progs), dif_vs_ini: comparables.inicial.diferencia_mclp,
    dif_vs_vig: comparables.vigente.diferencia_mclp}, comparables,
    cobertura: {sin_base_inicial: progs.filter(p => !disponible(p.ini_2026_mclp)).length,
      sin_base_vigente: progs.filter(p => !disponible(p.vig_2026_mclp)).length,
      sin_proyecto_2027: progs.filter(p => !disponible(p.proy_2027_mclp)).length,
      fuente_2027_secundaria: progs.filter(p => p.fuente_2027?.autoridad === 'secundaria').length}};
}

async function resolverEstatico(url) {
  if (url.includes('/presupuesto2027')) {
    if (!_cacheEstatico.presupuesto2027) {
      _cacheEstatico.presupuesto2027 = await cargarJSONEstatico('presupuesto2027.json');
    }
    const full = _cacheEstatico.presupuesto2027;
    const urlObj = new URL(url, 'http://localhost');
    const partida = urlObj.searchParams.get('partida') || '';
    const capitulo = urlObj.searchParams.get('capitulo') || '';
    const q = urlObj.searchParams.get('q') || '';
    const orden = urlObj.searchParams.get('orden') || '';
    const soloTangibles = urlObj.searchParams.get('solo_tangibles') === 'true';
    const subtitulo = urlObj.searchParams.get('subtitulo') || '';

    let progs = [...full.programas];
    if (partida) {
      progs = progs.filter(p => p.partida === partida || p.partida === partida.padStart(2, '0'));
    }
    if (capitulo) {
      progs = progs.filter(p => p.capitulo === capitulo || p.capitulo === capitulo.padStart(2, '0'));
    }
    if (soloTangibles) {
      progs = progs.filter(p => p.bajada_calle !== null && p.bajada_calle !== undefined);
    }
    if (subtitulo) {
      const subsReq = subtitulo.split(',').map(s => s.trim()).filter(Boolean);
      progs = progs.filter(p => {
        const pSubs = p.subtitulos || [];
        return subsReq.some(s => pSubs.includes(s) || pSubs.includes(s.padStart(2, '0')));
      });
    }
    if (q) {
      progs = progs.filter(p => coincidePrograma(p, q));
    }

    if (orden === 'mayor_recorte') {
      progs.sort((a, b) => (a.dif_vs_ini_mclp || 0) - (b.dif_vs_ini_mclp || 0));
    } else if (orden === 'mayor_aumento') {
      progs.sort((a, b) => (b.dif_vs_ini_mclp || 0) - (a.dif_vs_ini_mclp || 0));
    } else if (orden === 'monto_2027') {
      progs.sort((a, b) => (b.proy_2027_mclp || 0) - (a.proy_2027_mclp || 0));
    }

    return {
      total_programas: progs.length,
      ...resumenPresupuesto(progs),
      programas: progs
    };
  }

  if (url.includes('/programas')) {
    if (!_cacheEstatico.programas) {
      _cacheEstatico.programas = await cargarJSONEstatico('programas.json');
    }
    const full = _cacheEstatico.programas;
    const urlObj = new URL(url, 'http://localhost');
    const q = urlObj.searchParams.get('q') || '';
    const servicio = urlObj.searchParams.get('servicio') || '';

    let filtrados = [...full];
    if (servicio) filtrados = filtrados.filter(p => p.servicio === servicio);
    if (q) {
      const qNorm = normalizarTexto(q);
      filtrados = filtrados.filter(p => {
        const bolsa = normalizarTexto([p.nombre_programa, p.servicio, p.ministerio, p.descripcion].join(' '));
        return bolsa.includes(qNorm);
      });
    }
    return filtrados;
  }

  if (url.includes('/servicios')) {
    if (!_cacheEstatico.servicios) {
      _cacheEstatico.servicios = await cargarJSONEstatico('servicios.json');
    }
    return _cacheEstatico.servicios;
  }

  if (url.includes('/comparacion')) {
    if (!_cacheEstatico.comparacion) {
      _cacheEstatico.comparacion = await cargarJSONEstatico('comparacion.json');
    }
    return _cacheEstatico.comparacion;
  }

  if (url.includes('/equivalencias')) {
    if (!_cacheEstatico.equivalencias) {
      _cacheEstatico.equivalencias = await cargarJSONEstatico('equivalencias.json');
    }
    return _cacheEstatico.equivalencias;
  }

  if (url.includes('/recorrido/')) {
    if (!_cacheEstatico.recorridos) {
      _cacheEstatico.recorridos = await cargarJSONEstatico('recorridos.json');
    }
    const rawId = decodeURIComponent(url.split('/recorrido/')[1].split('?')[0]);
    const rec = _cacheEstatico.recorridos[rawId] || _cacheEstatico.recorridos[rawId.toLowerCase()] || _cacheEstatico.recorridos[normalizarTexto(rawId)];
    if (rec) return rec;
    for (const [k, v] of Object.entries(_cacheEstatico.recorridos)) {
      if (k.toLowerCase().includes(rawId.toLowerCase()) || rawId.toLowerCase().includes(k.toLowerCase())) {
        return v;
      }
    }
    throw new Error('Programa no encontrado');
  }

  if (url.includes('/articulado')) {
    if (!_cacheEstatico.articulado) {
      _cacheEstatico.articulado = await cargarJSONEstatico('matriz_articulado_2026_2027.json');
    }
    return _cacheEstatico.articulado;
  }

  if (url.includes('/comision-mixta')) {
    if (!_cacheEstatico.comisionMixta) {
      _cacheEstatico.comisionMixta = await cargarJSONEstatico('comision_mixta_hitos.json');
    }
    const full = _cacheEstatico.comisionMixta;
    const urlObj = new URL(url, 'http://localhost');
    const partida = urlObj.searchParams.get('partida') || '';
    const estado = urlObj.searchParams.get('estado') || '';
    let hitos = [...full];
    if (partida) hitos = hitos.filter(h => h.partida === partida || h.partida === partida.padStart(2, '0'));
    if (estado) hitos = hitos.filter(h => h.estado === estado);
    return { total: hitos.length, hitos: hitos };
  }

  throw new Error('Ruta estática no soportada: ' + url);
}

async function obtener(url) {
  const esLocal = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && (window.location.port === '8088' || window.location.port === '');
  if (esLocal && window.location.port === '8088') {
    try {
      const r = await fetch(url, { headers: { Accept: 'application/json' } });
      if (r.ok) return await r.json();
    } catch (e) {
      // Fallback si la API local no responde
    }
  }
  return await resolverEstatico(url);
}

// -------------------------------------------------------------
// Suite de Difusión y Acciones de Autor
// -------------------------------------------------------------
function compartir(canal) {
  const urlActual = window.location.href;
  const textoShare = 'Observatorio de prioridades fiscales y su impacto en los habitantes de Chile · Portal "De la Glosa a la Calle"';
  if (canal === 'whatsapp') {
    window.open('https://api.whatsapp.com/send?text=' + encodeURIComponent(textoShare + ' ' + urlActual), '_blank', 'noopener,noreferrer');
  } else if (canal === 'linkedin') {
    window.open('https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(urlActual), '_blank', 'noopener,noreferrer');
  } else if (canal === 'x') {
    window.open('https://twitter.com/intent/tweet?text=' + encodeURIComponent(textoShare) + '&url=' + encodeURIComponent(urlActual), '_blank', 'noopener,noreferrer');
  } else if (canal === 'copiar') {
    copiarTexto(urlActual);
  }
}

function copiarTexto(texto) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(texto).then(mostrarToastCopiado).catch(() => {
      copiarFallback(texto);
    });
  } else {
    copiarFallback(texto);
  }
}

function copiarFallback(texto) {
  try {
    const ta = document.createElement('textarea');
    ta.value = texto;
    ta.style.position = 'fixed';
    ta.style.top = '0';
    ta.style.left = '0';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  } catch (e) {
    // Si falla el comando del sistema, igual se notifica al usuario
  }
  mostrarToastCopiado();
}

function mostrarToastCopiado() {
  const toast = $('toast-copiado');
  if (!toast) return;
  toast.classList.add('visible');
  toast.setAttribute('aria-hidden', 'false');
  clearTimeout(window._toastTimeout);
  window._toastTimeout = setTimeout(() => {
    toast.classList.remove('visible');
    toast.setAttribute('aria-hidden', 'true');
  }, 2500);
}

function abrirAutor(id) {
  const url = id === 'linkedin' ? 'https://www.linkedin.com/in/edwardvega/' : 'https://evegat.cl';
  window.open(url, '_blank', 'noopener,noreferrer');
}

function abrirDipres(termino, partida) {
  let url = 'https://www.dipres.gob.cl/598/w3-propertyvalue-15186.html';
  if (termino) {
    url += '?q=' + encodeURIComponent(termino);
  } else if (partida) {
    url += '?partida=' + encodeURIComponent(partida);
  }
  window.open(url, '_blank', 'noopener,noreferrer');
}

function aplicarTema(t) {
  document.documentElement.setAttribute('data-tema', t);
  const txt = $('texto-tema');
  const ico = $('icono-tema');
  if (txt && ico) {
    if (t === 'oscuro') {
      ico.textContent = '☀️';
      txt.textContent = 'Claro';
    } else {
      ico.textContent = '🌙';
      txt.textContent = 'Oscuro';
    }
  }
}

function iniciarTema() {
  const guardado = localStorage.getItem('p149_tema');
  const prefiereOscuro = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  let temaActual = guardado || (prefiereOscuro ? 'oscuro' : 'claro');
  aplicarTema(temaActual);
  const btn = $('btn-tema-toggle');
  if (btn) {
    btn.addEventListener('click', () => {
      const actual = document.documentElement.getAttribute('data-tema') || (prefiereOscuro ? 'oscuro' : 'claro');
      const nuevo = actual === 'oscuro' ? 'claro' : 'oscuro';
      aplicarTema(nuevo);
      localStorage.setItem('p149_tema', nuevo);
    });
  }
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
      if (!localStorage.getItem('p149_tema')) {
        aplicarTema(e.matches ? 'oscuro' : 'claro');
      }
    });
  }
}

function iniciarSuiteDifusion() {
  iniciarTema();
  document.querySelectorAll('[data-share]').forEach(btn => {
    btn.addEventListener('click', () => compartir(btn.dataset.share));
  });
  document.querySelectorAll('[data-autor]').forEach(btn => {
    btn.addEventListener('click', () => abrirAutor(btn.dataset.autor));
  });
  const btnGlobalDipres = $('btn-portal-dipres');
  if (btnGlobalDipres) {
    btnGlobalDipres.addEventListener('click', () => abrirDipres('', ''));
  }
}

// -------------------------------------------------------------
// Navegación Superior por Pestañas (Vistas Modulares)
// -------------------------------------------------------------
function activarVista(pestana, cambiarHash) {
  const tabs = {
    'termometro': $('tab-termometro'),
    'articulado': $('tab-articulado'),
    'relato': $('tab-relato'),
    'ia': $('tab-ia'),
    'mixta': $('tab-mixta')
  };
  const paneles = {
    'termometro': $('vista-termometro'),
    'articulado': $('vista-articulado'),
    'relato': $('vista-relato'),
    'ia': $('vista-ia'),
    'mixta': $('vista-mixta')
  };

  for (const [k, tab] of Object.entries(tabs)) {
    if (tab) {
      const activo = k === pestana;
      tab.classList.toggle('activa', activo);
      tab.setAttribute('aria-selected', activo ? 'true' : 'false');
    }
  }

  for (const [k, panel] of Object.entries(paneles)) {
    if (panel) {
      panel.classList.toggle('activa', k === pestana);
    }
  }

  if (cambiarHash) {
    if (window.location.hash !== '#' + pestana) {
      window.location.hash = '#' + pestana;
    }
  }

  if (pestana === 'relato' && window.actualizarScrolly) {
    setTimeout(window.actualizarScrolly, 50);
  }
  if (pestana === 'mixta') {
    cargarRadarMixta();
  }
}

function sincronizarVistaPorHash() {
  const rawHash = (window.location.hash || '').replace('#', '').toLowerCase();
  let pestana = 'termometro';

  if (rawHash === 'articulado') {
    pestana = 'articulado';
  } else if (rawHash === 'relato' || rawHash === 'evidencia' || rawHash === 'comparacion' || rawHash === 'costos' || rawHash === 'preguntas' || rawHash === 'metodo' || rawHash.startsWith('paso-')) {
    pestana = 'relato';
  } else if (rawHash === 'ia' || rawHash === 'agentes') {
    pestana = 'ia';
  } else if (rawHash === 'mixta' || rawHash === 'seccion-mixta') {
    pestana = 'mixta';
  } else if (rawHash === 'termometro' || rawHash === 'comparador2027') {
    pestana = 'termometro';
  }

  activarVista(pestana, false);

  if (rawHash && rawHash !== pestana && $(rawHash)) {
    setTimeout(() => {
      const el = $(rawHash);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }, 120);
  }
}

function iniciarTabsSuperiores() {
  const tabButtons = [$('tab-termometro'), $('tab-articulado'), $('tab-relato'), $('tab-ia'), $('tab-mixta')].filter(Boolean);
  tabButtons.forEach((tab, idx) => {
    tab.addEventListener('click', () => {
      activarVista(tab.dataset.hash, true);
    });
    tab.addEventListener('keydown', (e) => {
      let nuevoIdx = -1;
      if (e.key === 'ArrowRight') nuevoIdx = (idx + 1) % tabButtons.length;
      else if (e.key === 'ArrowLeft') nuevoIdx = (idx - 1 + tabButtons.length) % tabButtons.length;
      else if (e.key === 'Home') nuevoIdx = 0;
      else if (e.key === 'End') nuevoIdx = tabButtons.length - 1;
      if (nuevoIdx !== -1) {
        e.preventDefault();
        tabButtons[nuevoIdx].focus();
        activarVista(tabButtons[nuevoIdx].dataset.hash, true);
      }
    });
  });

  window.addEventListener('hashchange', sincronizarVistaPorHash);
  sincronizarVistaPorHash();
}

// -------------------------------------------------------------
// Widget Macro Dual (Toggle +1,5% vs +2,7%)
// -------------------------------------------------------------
function iniciarWidgetMacroDual() {
  const btnEst = $('btn-macro-estimado');
  const btnLey = $('btn-macro-ley');
  const panEst = $('macro-panel-estimado');
  const panLey = $('macro-panel-ley');

  if (!btnEst || !btnLey || !panEst || !panLey) return;

  btnEst.addEventListener('click', () => {
    btnEst.classList.add('activa');
    btnLey.classList.remove('activa');
    panEst.style.display = 'block';
    panLey.style.display = 'none';
  });

  btnLey.addEventListener('click', () => {
    btnLey.classList.add('activa');
    btnEst.classList.remove('activa');
    panLey.style.display = 'block';
    panEst.style.display = 'none';
  });
}

// -------------------------------------------------------------
// Widget "Lo que más se mueve" (Top 5 Recortes y Aumentos)
// -------------------------------------------------------------
function irAFilaYAbrirDrawer(p) {
  activarVista('termometro', false);
  abrirRecorrido(p.codigo || p.nombre_programa);

  const codSanitizado = (p.codigo || '').replace(/[^a-zA-Z0-9_-]/g, '_');
  const scrollADestino = () => {
    const fila = $('fila-prog-' + codSanitizado);
    if (fila) {
      const acc = fila.closest('details');
      if (acc) acc.open = true;
      fila.scrollIntoView({ behavior: 'smooth', block: 'center' });
      fila.classList.add('fila-destacada');
      setTimeout(() => fila.classList.remove('fila-destacada'), 2500);
    }
  };

  const filaExistente = $('fila-prog-' + codSanitizado);
  if (filaExistente) {
    scrollADestino();
  } else {
    if ($('busqueda-2027')) $('busqueda-2027').value = '';
    filtroPartida2027 = '';
    filtroTangible2027 = 'todos';
    filtroSubtitulo2027 = '';
    if ($('selector-partida-2027')) $('selector-partida-2027').value = '';
    document.querySelectorAll('.pill-btn[data-partida]').forEach(b => b.classList.toggle('activa', b.dataset.partida === ''));
    document.querySelectorAll('.btn-tangible').forEach(b => b.classList.toggle('activa', b.dataset.tangible === 'todos'));
    document.querySelectorAll('.chip-sub').forEach(b => b.classList.toggle('activa', !b.dataset.sub));
    cargarTermometro2027().then(scrollADestino);
  }
}

function cargarLoQueMasSeMueve(programas) {
  const listaRecortes = $('top-recortes-lista');
  const listaAumentos = $('top-aumentos-lista');
  if (!listaRecortes || !listaAumentos) return;

  listaRecortes.replaceChildren();
  listaAumentos.replaceChildren();

  const conDif = programas.filter(p => typeof p.dif_vs_ini_mclp === 'number' && Number.isFinite(p.dif_vs_ini_mclp));
  const recortes = [...conDif].sort((a, b) => (a.dif_vs_ini_mclp || 0) - (b.dif_vs_ini_mclp || 0)).slice(0, 5);
  const aumentos = [...conDif].sort((a, b) => (b.dif_vs_ini_mclp || 0) - (a.dif_vs_ini_mclp || 0)).slice(0, 5);

  const crearCardMovimiento = (p, esRecorte) => {
    const card = elemento('div', undefined, 'movimiento-item ' + (esRecorte ? 'item-recorte' : 'item-aumento'));
    card.setAttribute('tabindex', '0');
    card.setAttribute('role', 'button');
    card.setAttribute('aria-label', p.nombre_programa + ': ' + (esRecorte ? 'recorte de $' : 'aumento de $') + numero(Math.abs(p.dif_vs_ini_mclp)) + ' M$');

    const filaSup = elemento('div', undefined, 'movimiento-fila-sup');
    const badgeCod = elemento('span', p.codigo, 'meta movimiento-cod');
    const badgeMonto = elemento('span', (esRecorte ? '-$' : '+$') + numero(Math.abs(p.dif_vs_ini_mclp)) + ' M$', 'badge-var ' + (esRecorte ? 'var-neg' : 'var-pos'));
    filaSup.append(badgeCod, badgeMonto);

    const tit = elemento('div', p.nombre_programa, 'movimiento-titulo');
    const min = elemento('div', p.nombre_partida || ('Partida ' + p.partida), 'meta movimiento-partida');

    card.append(filaSup, tit, min);

    const onClick = () => {
      irAFilaYAbrirDrawer(p);
    };
    card.addEventListener('click', onClick);
    card.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        onClick();
      }
    });

    return card;
  };

  for (const p of recortes) listaRecortes.append(crearCardMovimiento(p, true));
  for (const p of aumentos) listaAumentos.append(crearCardMovimiento(p, false));
}

// -------------------------------------------------------------
// Catálogo Local y Consultas de Evidencia
// -------------------------------------------------------------
let turno = 0;
async function buscar() {
  const actual = ++turno;
  const parametros = new URLSearchParams();
  if ($('busqueda').value.trim()) parametros.set('q', $('busqueda').value.trim());
  if ($('servicio').value) parametros.set('servicio', $('servicio').value);
  $('estado-programas').textContent = 'Buscando…';
  try {
    const filas = await obtener('/api/programas?' + parametros);
    if (actual !== turno) return;
    $('resultados').replaceChildren();
    for (const f of filas) {
      const a = elemento('article', undefined, 'resultado');
      a.append(elemento('p', f.servicio || 'Servicio no reportado', 'meta'), elemento('h3', f.nombre_programa || 'Nombre no reportado'), elemento('p', f.ministerio || 'Institución no reportada'));
      if (f.descripcion) {
        const desc = elemento('p', f.descripcion.substring(0, 180) + '…', 'meta');
        desc.style.color = '#33413e';
        a.append(desc);
      }
      const btn = elemento('button', 'Ver Recorrido →', 'btn-recorrido');
      btn.addEventListener('click', () => abrirRecorrido(f.id_bips || f.nombre_programa));
      a.append(btn);
      $('resultados').append(a);
    }
    $('estado-programas').textContent = filas.length ? filas.length + ' programas en el catálogo.' : 'Sin coincidencias. Prueba menos términos o cambia el servicio; no demuestra ausencia de presupuesto.';
  } catch (e) {
    if (actual === turno) {
      $('resultados').replaceChildren();
      $('estado-programas').textContent = 'El catálogo no está disponible. Reintenta o descarga la fuente local.';
    }
  }
}
$('filtros').addEventListener('submit', e => { e.preventDefault(); buscar(); });
$('servicio').addEventListener('change', buscar);

async function servicios() {
  try {
    const rows = await obtener('/api/servicios');
    for (const s of rows) {
      const o = elemento('option', s);
      o.value = s;
      $('servicio').append(o);
    }
  } catch (e) {
    $('servicio').disabled = true;
    $('servicio').title = 'Filtro no disponible; usa el buscador';
  }
}

const clp = new Intl.NumberFormat('es-CL', { maximumFractionDigits: 2 });
const numero = v => v === null || v === undefined ? 'No disponible' : clp.format(v);

async function comparar() {
  try {
    const r = await obtener('/api/comparacion');
    $('estado-comparacion').textContent = r.motivo;
    if (r.datos && r.datos.length) {
      for (const f of r.datos) {
        const a = elemento('article', undefined, 'presupuesto');
        a.append(elemento('h3', [f.partida, f.capitulo, f.programa, f.subtitulo, f.item, f.asignacion].join(' · ')), elemento('p', f.denominacion_2026 || f.denominacion_2025 || 'Denominación no reportada'));
        const dl = elemento('dl');
        for (const [label, v] of [['Monto 2025 (' + (f.unidad_2025 || 'unidad no reportada') + ' / ' + (f.moneda_2025 || 'moneda no reportada') + ')', f.monto_2025], ['Monto 2026 (' + (f.unidad_2026 || 'unidad no reportada') + ' / ' + (f.moneda_2026 || 'moneda no reportada') + ')', f.monto_2026], ['Variación nominal (%)', f.variacion_nominal_pct], ['Variación real (%)', f.variacion_real_pct]]) dl.append(elemento('dt', label), elemento('dd', numero(v)));
        a.append(dl, elemento('p', 'Estado: ' + f.estado, 'meta'));
        $('presupuestos').append(a);
      }
    } else {
      $('estado-comparacion').textContent = 'Comparación disponible en el Termómetro interactivo 2027 vs 2026.';
    }
  } catch (e) {
    $('estado-comparacion').textContent = 'Comparación disponible en el Termómetro de la Ley 2027.';
  }
}

async function costos() {
  try {
    const r = await obtener('/api/equivalencias');
    $('estado-costos').textContent = r.grupos && r.grupos.length ? 'Referencias observacionales por grupo comparable.' : 'Sin costos de referencia verificados con cantidad, territorio y período. No disponible para equivalencias.';
    if (r.grupos) {
      for (const f of r.grupos) {
        const a = elemento('article', undefined, 'resultado');
        a.append(elemento('h3', f.servicio), elemento('p', f.territorio + ' · ' + f.periodo), elemento('p', 'n=' + f.n + ' · Unidad: ' + f.unidad + ' · ' + f.moneda), elemento('p', 'P25: ' + numero(f.p25) + ' · Mediana: ' + numero(f.p50) + ' · P75: ' + numero(f.p75)), elemento('p', 'Desviación estándar: ' + numero(f.desviacion_estandar)), elemento('p', f.limite, 'meta'));
        $('referencias').append(a);
      }
    }
  } catch (e) {
    $('estado-costos').textContent = 'No se pudo leer el catálogo de referencia. No se muestran estimaciones de reemplazo.';
  }
}

// -------------------------------------------------------------
// Drawer de Recorrido Presupuestario
// -------------------------------------------------------------
async function abrirRecorrido(id) {
  $('drawer').classList.add('abierto');
  $('drawer-backdrop').classList.add('abierto');
  $('drawer').setAttribute('aria-hidden', 'false');
  $('recorrido-titulo').textContent = 'Cargando recorrido…';
  $('recorrido-descripcion').textContent = '…';
  $('recorrido-estaciones').replaceChildren();
  const pinnedGlosa = $('drawer-pinned-glosa');
  if (pinnedGlosa) pinnedGlosa.replaceChildren();

  try {
    const data = await obtener('/api/recorrido/' + encodeURIComponent(id));
    const p = data.programa;
    $('recorrido-servicio').textContent = p.servicio || p.ministerio || 'Servicio Público';
    $('recorrido-titulo').textContent = p.nombre_programa;
    $('recorrido-descripcion').textContent = p.descripcion || 'Sin descripción oficial en BIPS.';

    if (pinnedGlosa) {
      pinnedGlosa.replaceChildren();
      const pTit = elemento('div', undefined, 'pinned-glosa-titulo');
      pTit.append(elemento('span', '👤'), elemento('strong', 'Dotación y Personal Autorizado (Subtítulo 21)'));
      pinnedGlosa.append(pTit);

      let progDetalle = null;
      if (_cacheEstatico.presupuesto2027 && _cacheEstatico.presupuesto2027.programas) {
        progDetalle = _cacheEstatico.presupuesto2027.programas.find(x => x.codigo === id || x.nombre_programa === p.nombre_programa || x.codigo === p.codigo);
      }
      const tieneDot = progDetalle ? progDetalle.tiene_dotacion : (p.asignacion && p.asignacion.includes('21'));
      const montoDot = progDetalle ? progDetalle.monto_personal_2027_mclp : null;

      if (tieneDot) {
        const cifra = elemento('div', montoDot ? '$' + numero(montoDot) + ' M$ asignados a Personal 2027' : 'Dotación máxima de personal fijada por Ley', 'pinned-glosa-cifra');
        const desc = elemento('p', undefined, 'pinned-glosa-texto');
        desc.append(
          elemento('strong', 'Dotación autorizada por Ley: '),
          document.createTextNode('Fijada por glosa presupuestaria anual de personal. '),
          elemento('br'),
          elemento('strong', 'Límite legal a honorarios: '),
          document.createTextNode('Regulado bajo el Artículo 15 del Proyecto 2027 (fijado en 1.500 traspasos máximos). '),
          elemento('br'),
          elemento('strong', 'Glosa 01 de dotación: '),
          document.createTextNode('"Fija dotación máxima de personal y límite máximo de contrataciones a honorarios conforme al D.L. N° 249 y Ley N° 21.796."')
        );
        pinnedGlosa.append(cifra, desc);
      } else {
        const desc = elemento('p', 'Este programa no cuenta con asignación presupuestaria directa en Subtítulo 21 (Personal). Opera mediante transferencias o adquisiciones (Subtítulos 22 o 24).', 'pinned-glosa-texto');
        pinnedGlosa.append(desc);
      }
    }

    for (const est of data.estaciones) {
      const card = elemento('div', undefined, 'estacion-card ' + (est.tipo === 'calle' ? 'calle' : ''));
      card.append(elemento('div', String(est.estacion), 'estacion-num'));
      const cuerpo = elemento('div', undefined, 'estacion-cuerpo');
      cuerpo.append(elemento('div', est.fase, 'estacion-fase'), elemento('h4', est.titulo, 'estacion-titulo'), elemento('p', est.detalle, 'estacion-detalle'));
      if (est.costo_unitario_referencia) {
        cuerpo.append(elemento('p', 'Costo Unitario Ref.: $' + numero(est.costo_unitario_referencia), 'meta'));
      }
      if (est.dilema_calle) {
        const d = elemento('div', undefined, 'dilema-box');
        d.append(elemento('strong', 'El dilema en la calle: '), elemento('span', est.dilema_calle));
        cuerpo.append(d);
      }
      card.append(cuerpo);
      $('recorrido-estaciones').append(card);
    }

    const btnDipresDrawer = elemento('button', '📄 Consultar documento oficial en portal DIPRES ↗', 'btn-dipres-drawer');
    btnDipresDrawer.title = 'Abrir búsqueda de este programa en la web oficial de DIPRES';
    btnDipresDrawer.addEventListener('click', () => abrirDipres(p.nombre_programa || p.codigo, p.partida));
    $('recorrido-estaciones').append(btnDipresDrawer);
  } catch (err) {
    $('recorrido-titulo').textContent = 'Recorrido no disponible';
    $('recorrido-descripcion').textContent = 'No se pudo cargar el flujo de este programa: ' + err.message;
  }
}

function cerrarRecorrido() {
  $('drawer').classList.remove('abierto');
  $('drawer-backdrop').classList.remove('abierto');
  $('drawer').setAttribute('aria-hidden', 'true');
}
$('drawer-cerrar').addEventListener('click', cerrarRecorrido);
$('drawer-backdrop').addEventListener('click', cerrarRecorrido);
document.addEventListener('keydown', e => { if (e.key === 'Escape') cerrarRecorrido(); });

// Scrollytelling
if ('IntersectionObserver' in window) {
  const pasos = [...document.querySelectorAll('[data-paso]')];
  const actualizar = () => {
    const punto = innerWidth <= 680 ? document.querySelector('.escena').getBoundingClientRect().bottom + 80 : innerHeight * .4;
    const actual = pasos.find(p => {
      const r = p.getBoundingClientRect();
      return r.top <= punto && r.bottom > punto;
    });
    if (actual) document.querySelectorAll('[data-capa]').forEach(g => g.classList.toggle('activa', g.dataset.capa === actual.dataset.paso));
  };
  window.actualizarScrolly = actualizar;
  const observador = new IntersectionObserver(actualizar, { threshold: [0, .25, .5, .75, 1] });
  pasos.forEach(p => observador.observe(p));
  window.addEventListener('scroll', actualizar, { passive: true });
  window.addEventListener('resize', actualizar, { passive: true });
}

$('form-pregunta').addEventListener('submit', async e => {
  e.preventDefault();
  const boton = $('registrar-pregunta');
  boton.disabled = true;
  $('estado-pregunta').textContent = 'Registrando…';
  try {
    const r = await fetch('/api/preguntas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pregunta: $('pregunta').value })
    });
    if(!r.ok){
      $('estado-pregunta').textContent=r.status===429?'Espera antes de registrar otra pregunta.':r.status===422?'Revisa la pregunta: entre 4 y 500 caracteres de texto.':'No se pudo confirmar el registro. Conserva tu texto y reintenta.';
      return;
    }
    const dato = await r.json();
    $('estado-pregunta').textContent = 'Pregunta registrada con folio ' + dato.id + '. Pendiente de revisión.';
    $('pregunta').value = '';
  } catch (e) {
    $('estado-pregunta').textContent = 'Sin confirmación de registro. Conserva tu texto y reintenta.';
  } finally {
    boton.disabled = false;
  }
});

// -------------------------------------------------------------
// Termómetro Presupuesto 2027 vs 2026 y Buscador Reactivo
// -------------------------------------------------------------
let filtroPartida2027 = '';
let filtroCapitulo2027 = '';
let orden2027 = 'mayor_recorte';
let filtroTangible2027 = 'todos';
let filtroSubtitulo2027 = '';
let _cacheHitosMixta = null;

function poblarSelectorCapitulos(codPartida) {
  const selCap = $('selector-capitulo-2027');
  if (!selCap) return;
  selCap.replaceChildren();

  if (!codPartida) {
    selCap.disabled = true;
    const optDef = elemento('option', 'Todos los Capítulos / Servicios…');
    optDef.value = '';
    selCap.append(optDef);
    selCap.value = '';
    filtroCapitulo2027 = '';
    return;
  }

  selCap.disabled = false;
  const optTodos = elemento('option', 'Todos los Capítulos de esta cartera…');
  optTodos.value = '';
  selCap.append(optTodos);

  let progs = [];
  if (_cacheEstatico.presupuesto2027 && _cacheEstatico.presupuesto2027.programas) {
    progs = _cacheEstatico.presupuesto2027.programas;
  }
  const capsMap = new Map();
  for (const p of progs) {
    const pPartida = String(p.partida || '').padStart(2, '0');
    if (pPartida === codPartida.padStart(2, '0')) {
      const cCod = String(p.capitulo || '').padStart(2, '0');
      const cNom = p.nombre_capitulo || ('Capítulo ' + cCod);
      if (!capsMap.has(cCod)) {
        capsMap.set(cCod, cNom);
      }
    }
  }

  const codsOrdenados = [...capsMap.keys()].sort();
  for (const cCod of codsOrdenados) {
    const opt = elemento('option', `Cap. ${cCod} · ${capsMap.get(cCod)}`);
    opt.value = cCod;
    selCap.append(opt);
  }
  selCap.value = filtroCapitulo2027;
}

async function cargarTermometro2027() {
  const contenedor = $('contenedor-acordeon-2027');
  if (!contenedor) return;
  contenedor.replaceChildren();
  $('estado-2027').textContent = 'Cargando comparación presupuestaria 2027…';
  $('cobertura-programas').textContent = 'Consultando la cobertura de la selección…';

  const params = new URLSearchParams();
  if (filtroPartida2027) params.set('partida', filtroPartida2027);
  if (filtroCapitulo2027) params.set('capitulo', filtroCapitulo2027);
  if (orden2027) params.set('orden', orden2027);
  if (filtroTangible2027 === 'si') params.set('solo_tangibles', 'true');
  if (filtroSubtitulo2027) params.set('subtitulo', filtroSubtitulo2027);
  const busq = $('busqueda-2027') ? $('busqueda-2027').value.trim() : '';
  if (busq) params.set('q', busq);

  try {
    const res = await obtener('/api/presupuesto2027?' + params);
    const partidasMostradas = new Set(res.programas.map(p => p.partida).filter(Boolean)).size;

    // Cargar hitos de Comisión Mixta para alertas cruzadas
    if (!_cacheHitosMixta) {
      try {
        const dataMixta = await obtener('/api/comision-mixta');
        _cacheHitosMixta = dataMixta.hitos || [];
      } catch (e) {
        _cacheHitosMixta = [];
      }
    }
    const hitosPorProg = new Map();
    for (const h of (_cacheHitosMixta || [])) {
      if (h.programa_codigo) hitosPorProg.set(h.programa_codigo, h);
    }

    // Actualizar contador reactivo de búsqueda
    const badgeContador = $('badge-contador-busqueda');
    if (badgeContador) {
      const capTxt = filtroCapitulo2027 ? ` (Capítulo ${filtroCapitulo2027})` : '';
      badgeContador.textContent = `${res.programas.length} ${res.programas.length === 1 ? 'programa encontrado' : 'programas encontrados'}${capTxt} en ${partidasMostradas} ${partidasMostradas === 1 ? 'ministerio' : 'ministerios'}`;
    }

    $('cobertura-programas').textContent = 'Selección mostrada: ' + res.programas.length +
      (res.programas.length === 1 ? ' programa presupuestario en ' : ' programas presupuestarios en ') +
      partidasMostradas + (partidasMostradas === 1 ? ' partida.' : ' partidas.') + ' Los filtros actualizan esta cobertura.';
    $('estado-2027').textContent = res.total_programas + ' programas · ' + res.comparables.inicial.total_programas + ' con base inicial · ' + res.cobertura.sin_base_inicial + ' sin contraparte 2026 · ' + res.cobertura.fuente_2027_secundaria + ' con fuente secundaria. Sumas de programas, sin consolidar transferencias.';

    if ($('kpi-total-proy')) {
      const total = res.totales_mclp.proyecto_2027;
      $('kpi-total-proy').textContent = total === null ? 'No disponible' : '$' + (total / 1e9).toLocaleString('es-CL', {maximumFractionDigits: 2}) + ' billones';
      const comp = res.comparables.inicial, dif = comp.diferencia_mclp, pct = comp.variacion_pct;
      const signClp = dif >= 0 ? '+$' : '-$';
      const pctStr = pct === null ? ' · porcentaje no calculable' : ' (' + (pct >= 0 ? '+' : '') + pct.toLocaleString('es-CL', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + '%)';
      $('kpi-var-ini').textContent = dif === null ? 'Sin base comparable' :
        signClp + numero(Math.abs(Math.round(dif / 1000))) + ' millones' +
        pctStr + ' · ' + comp.total_programas + ' pares de programas';
      $('kpi-var-ini').className = 'badge ' + (dif === null ? '' : dif >= 0 ? 'badge-sube' : 'badge-baja');
    }

    // Poblar módulo "Lo que más se mueve"
    if (_cacheEstatico.presupuesto2027 && _cacheEstatico.presupuesto2027.programas) {
      cargarLoQueMasSeMueve(_cacheEstatico.presupuesto2027.programas);
    } else {
      cargarLoQueMasSeMueve(res.programas);
    }

    if (res.programas.length === 0) {
      const emptyDiv = elemento('div', 'No se encontraron programas con los filtros seleccionados.', 'meta');
      emptyDiv.style.padding = '2rem 1rem';
      emptyDiv.style.textAlign = 'center';
      contenedor.append(emptyDiv);
      return;
    }

    // Agrupar por Partida
    const agrupado = new Map();
    for (const p of res.programas) {
      const codPartida = p.partida || '00';
      if (!agrupado.has(codPartida)) {
        agrupado.set(codPartida, {
          partida: codPartida,
          nombre_partida: p.nombre_partida || ('Partida ' + codPartida),
          programas: []
        });
      }
      agrupado.get(codPartida).programas.push(p);
    }

    const abrirTodos = Boolean(filtroPartida2027 || busq || agrupado.size <= 2);

    for (const [codPartida, grupo] of agrupado.entries()) {
      const details = elemento('details', undefined, 'acordeon-partida');
      if (abrirTodos) {
        details.open = true;
      }

      const summary = elemento('summary', undefined, 'acordeon-summary');
      const divTit = elemento('div', undefined, 'acordeon-titulo');
      divTit.append(elemento('span', '🏛️ Partida ' + codPartida + ': ' + grupo.nombre_partida));

      const divMeta = elemento('div', undefined, 'acordeon-meta');
      const totalPartida2027 = grupo.programas.reduce((acc, curr) => acc + (typeof curr.proy_2027_mclp === 'number' ? curr.proy_2027_mclp : 0), 0);
      const strMonto = totalPartida2027 >= 1e9
        ? '$' + (totalPartida2027 / 1e9).toLocaleString('es-CL', {maximumFractionDigits: 2}) + ' billones'
        : '$' + numero(Math.round(totalPartida2027 / 1000)) + ' millones';

      const btnDipresPartida = elemento('button', 'DIPRES Partida ' + codPartida + ' ↗', 'btn-dipres-partida');
      btnDipresPartida.title = 'Abrir documentación oficial de la Partida ' + codPartida + ' en portal DIPRES';
      btnDipresPartida.addEventListener('click', (ev) => {
        ev.stopPropagation();
        abrirDipres('', codPartida);
      });

      divMeta.append(
        elemento('span', grupo.programas.length + (grupo.programas.length === 1 ? ' programa' : ' programas')),
        elemento('span', strMonto),
        btnDipresPartida
      );
      summary.append(divTit, divMeta);
      details.append(summary);

      const divCont = elemento('div', undefined, 'acordeon-contenido');
      const tablaWrap = elemento('div', undefined, 'tabla-wrapper');
      const tabla = elemento('table', undefined, 'tabla-comp');

      const thead = elemento('thead');
      const trHead = elemento('tr');
      trHead.append(
        elemento('th', 'Código', 'th-cod'),
        elemento('th', 'Programa y bajada a la calle'),
        elemento('th', 'Inicial 2026', 'num th-monto'),
        elemento('th', 'Vigente 2026', 'num th-monto'),
        elemento('th', 'Propuesta 2027', 'num th-monto'),
        elemento('th', 'Var. Inicial', 'num th-var'),
        elemento('th', 'Var. Vigente', 'num th-var'),
        elemento('th', 'Detalle', 'num th-accion')
      );
      thead.append(trHead);
      tabla.append(thead);

      const tbody = elemento('tbody');
      let ultimoCapitulo = null;
      const capitulosEnGrupo = new Set(grupo.programas.map(p => p.capitulo)).size;

      for (const p of grupo.programas) {
        // Separador visual de Capítulos si hay múltiples servicios en la cartera
        if (!filtroCapitulo2027 && capitulosEnGrupo > 1 && p.capitulo !== ultimoCapitulo) {
          ultimoCapitulo = p.capitulo;
          const trSep = elemento('tr', undefined, 'fila-separador-capitulo');
          const tdSep = elemento('td');
          tdSep.colSpan = 8;
          const innerSep = elemento('div', undefined, 'separador-capitulo-inner');
          innerSep.append(
            elemento('span', '📂 Cap. ' + p.capitulo, 'cap-tag'),
            elemento('span', p.nombre_capitulo || ('Capítulo ' + p.capitulo))
          );
          trSep.append(tdSep);
          tbody.append(trSep);
        }

        const tr = elemento('tr');
        if (p.codigo) {
          tr.id = 'fila-prog-' + p.codigo.replace(/[^a-zA-Z0-9_-]/g, '_');
          tr.dataset.codigo = p.codigo;
        }

        const tdCod = elemento('td', p.codigo, 'meta td-cod');
        const tdProg = elemento('td', undefined, 'td-prog');
        tdProg.append(elemento('strong', p.nombre_programa));
        if (p.tiene_dotacion) {
          tdProg.append(document.createTextNode(' '), elemento('span', '👤 Dotación', 'badge-dotacion'));
        }
        tdProg.append(elemento('div', p.nombre_capitulo + ' · ' + p.nombre_partida, 'meta'));
        if (p.bajada_calle) {
          const b = elemento('div', p.bajada_calle.icono + ' Escenario: ' + p.bajada_calle.impacto_texto, 'badge-calle ' + (p.bajada_calle.signo === '+' ? 'calle-sube' : 'calle-baja'));
          b.title = p.bajada_calle.limite_metodologico + ' Base: ' + p.bajada_calle.base_comparacion + '. Costo supuesto: $' + numero(p.bajada_calle.costo_unitario_clp);
          tdProg.append(b);
        }

        // Alerta si el programa está en controversia en Comisión Mixta
        const hitoAsoc = hitosPorProg.get(p.codigo);
        if (hitoAsoc) {
          const btnMixta = elemento('button', '⚡ En debate Mixta: ' + hitoAsoc.estado, 'badge-alerta-mixta');
          btnMixta.title = 'Ver controversia en Comisión Mixta: ' + hitoAsoc.tema_o_glosa;
          btnMixta.addEventListener('click', (ev) => {
            ev.stopPropagation();
            activarVista('mixta', true);
            const cardHito = $('hito-' + hitoAsoc.id);
            if (cardHito) {
              cardHito.scrollIntoView({ behavior: 'smooth' });
              cardHito.classList.add('fila-destacada');
              setTimeout(() => cardHito.classList.remove('fila-destacada'), 2500);
            }
          });
          tdProg.append(btnMixta);
        }

        const divFuente = elemento('div', undefined, 'meta');
        if (p.fuente_2027) {
          divFuente.append(document.createTextNode('Fuente: ' + p.fuente_2027.archivo +
            (p.fuente_2027.pagina ? ' · pág. ' + p.fuente_2027.pagina : '')));
        }
        const btnDipresProg = elemento('button', 'DIPRES ↗', 'btn-dipres-link');
        btnDipresProg.title = 'Consultar fuente oficial de ' + p.nombre_programa + ' en DIPRES';
        btnDipresProg.addEventListener('click', (ev) => {
          ev.stopPropagation();
          abrirDipres(p.nombre_programa || p.codigo, p.partida);
        });
        divFuente.append(btnDipresProg);
        tdProg.append(divFuente);
        const tdIni = elemento('td', p.ini_2026_mclp === null ? 'No disponible' : '$' + numero(p.ini_2026_mclp), 'num td-monto');
        const tdVig = elemento('td', p.vig_2026_mclp === null ? 'No disponible' : '$' + numero(p.vig_2026_mclp), 'num td-monto');
        const tdProy = elemento('td', p.proy_2027_mclp === null ? 'No disponible' : '$' + numero(p.proy_2027_mclp), 'num td-monto');

        const formatearVarBadge = (dif, pct, baseMclp) => {
          const wrap = elemento('div', undefined, 'celda-var');
          if (pct !== null) {
            const signClp = dif >= 0 ? '+$' : '-$';
            const pctStr = (pct >= 0 ? '+' : '') + pct.toLocaleString('es-CL', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + '%';
            const badge = elemento('span', pctStr, 'badge-var ' + (dif >= 0 ? 'var-pos' : 'var-neg'));
            const sub = elemento('span', signClp + numero(Math.abs(dif)), 'sub-monto');
            wrap.append(badge, sub);
          } else {
            const txt = baseMclp === null ? 'Sin base' : 'Base cero';
            const badge = elemento('span', txt, 'badge-var var-neutral');
            wrap.append(badge);
            if (baseMclp !== null && dif !== null && dif !== 0) {
              const signClp = dif >= 0 ? '+$' : '-$';
              wrap.append(elemento('span', signClp + numero(Math.abs(dif)), 'sub-monto'));
            }
          }
          return wrap;
        };

        const tdDifIni = elemento('td', undefined, 'num td-var');
        tdDifIni.append(formatearVarBadge(p.dif_vs_ini_mclp, p.pct_vs_ini, p.ini_2026_mclp));

        const tdDifVig = elemento('td', undefined, 'num td-var');
        tdDifVig.append(formatearVarBadge(p.dif_vs_vig_mclp, p.pct_vs_vig, p.vig_2026_mclp));

        const tdAccion = elemento('td', undefined, 'num td-accion');
        const btn = elemento('button', 'Recorrido →', 'btn-mini-rec');
        btn.addEventListener('click', () => abrirRecorrido(p.codigo || p.nombre_programa));
        tdAccion.append(btn);

        tr.append(tdCod, tdProg, tdIni, tdVig, tdProy, tdDifIni, tdDifVig, tdAccion);
        tbody.append(tr);
      }
      tabla.append(tbody);
      tablaWrap.append(tabla);
      divCont.append(tablaWrap);
      details.append(divCont);
      contenedor.append(details);
    }
  } catch (e) {
    $('estado-2027').textContent = 'Error al consultar la comparativa presupuestaria 2027.';
    $('cobertura-programas').textContent = 'Cobertura no disponible: no se pudo cargar la selección.';
  }
}

function iniciarControles2027() {
  const selPartida = $('selector-partida-2027');
  const selCap = $('selector-capitulo-2027');

  if (selPartida) {
    selPartida.addEventListener('change', () => {
      filtroPartida2027 = selPartida.value;
      filtroCapitulo2027 = '';
      poblarSelectorCapitulos(filtroPartida2027);
      document.querySelectorAll('.pill-btn[data-partida]').forEach(b => {
        b.classList.toggle('activa', b.dataset.partida === filtroPartida2027);
      });
      cargarTermometro2027();
    });
  }

  if (selCap) {
    selCap.addEventListener('change', () => {
      filtroCapitulo2027 = selCap.value;
      cargarTermometro2027();
    });
  }

  document.querySelectorAll('.pill-btn[data-partida]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.pill-btn[data-partida]').forEach(b => b.classList.remove('activa'));
      btn.classList.add('activa');
      filtroPartida2027 = btn.dataset.partida;
      filtroCapitulo2027 = '';
      if (selPartida) selPartida.value = filtroPartida2027;
      poblarSelectorCapitulos(filtroPartida2027);
      cargarTermometro2027();
    });
  });

  if ($('orden-2027')) {
    $('orden-2027').addEventListener('change', e => {
      orden2027 = e.target.value;
      cargarTermometro2027();
    });
  }

  // Buscador reactivo sobre los 515 programas con reset de filtros restrictivos
  if ($('busqueda-2027')) {
    let t;
    $('busqueda-2027').addEventListener('input', () => {
      const qVal = $('busqueda-2027').value.trim();
      if (qVal) {
        if (filtroPartida2027) {
          filtroPartida2027 = '';
          filtroCapitulo2027 = '';
          if (selPartida) selPartida.value = '';
          if (selCap) { selCap.value = ''; selCap.disabled = true; }
          document.querySelectorAll('.pill-btn[data-partida]').forEach(b => b.classList.toggle('activa', b.dataset.partida === ''));
        }
        if (filtroTangible2027 !== 'todos') {
          filtroTangible2027 = 'todos';
          document.querySelectorAll('.btn-tangible').forEach(b => b.classList.toggle('activa', b.dataset.tangible === 'todos'));
        }
        if (filtroSubtitulo2027) {
          filtroSubtitulo2027 = '';
          document.querySelectorAll('.chip-sub').forEach(b => b.classList.toggle('activa', !b.dataset.sub));
        }
      }
      clearTimeout(t);
      t = setTimeout(cargarTermometro2027, 200);
    });
  }

  // Botón de limpieza rápida de búsqueda
  if ($('btn-limpiar-busqueda')) {
    $('btn-limpiar-busqueda').addEventListener('click', () => {
      if ($('busqueda-2027')) $('busqueda-2027').value = '';
      filtroPartida2027 = '';
      filtroCapitulo2027 = '';
      filtroTangible2027 = 'todos';
      filtroSubtitulo2027 = '';
      if (selPartida) selPartida.value = '';
      if (selCap) { selCap.value = ''; selCap.disabled = true; }
      document.querySelectorAll('.pill-btn[data-partida]').forEach(b => b.classList.toggle('activa', b.dataset.partida === ''));
      document.querySelectorAll('.btn-tangible').forEach(b => b.classList.toggle('activa', b.dataset.tangible === 'todos'));
      document.querySelectorAll('.chip-sub').forEach(b => b.classList.toggle('activa', !b.dataset.sub));
      cargarTermometro2027().then(() => {
        document.querySelectorAll('#contenedor-acordeon-2027 .acordeon-partida').forEach(d => {
          d.open = false;
        });
      });
    });
  }

  // R1 Filtro de Tangibilidad Cívica
  document.querySelectorAll('.btn-tangible[data-tangible]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-tangible').forEach(b => b.classList.remove('activa'));
      btn.classList.add('activa');
      filtroTangible2027 = btn.dataset.tangible;
      cargarTermometro2027();
    });
  });

  // R1 Chips de Subtítulos DIPRES
  const chipsSub = document.querySelectorAll('.chip-sub[data-sub]');
  chipsSub.forEach(chip => {
    chip.addEventListener('click', () => {
      const subVal = chip.dataset.sub;
      if (!subVal) {
        chipsSub.forEach(c => c.classList.remove('activa'));
        chip.classList.add('activa');
        filtroSubtitulo2027 = '';
      } else {
        const chipTodos = document.querySelector('.chip-sub[data-sub=""]');
        if (chipTodos) chipTodos.classList.remove('activa');
        chip.classList.toggle('activa');
        const activos = Array.from(document.querySelectorAll('.chip-sub[data-sub].activa'))
          .map(c => c.dataset.sub)
          .filter(Boolean);
        if (activos.length === 0) {
          if (chipTodos) chipTodos.classList.add('activa');
          filtroSubtitulo2027 = '';
        } else {
          filtroSubtitulo2027 = activos.join(',');
        }
      }
      cargarTermometro2027();
    });
  });

  // Controles de Expandir / Colapsar todas las carteras
  if ($('btn-expandir-todos')) {
    $('btn-expandir-todos').addEventListener('click', () => {
      document.querySelectorAll('#contenedor-acordeon-2027 .acordeon-partida').forEach(d => {
        d.open = true;
      });
    });
  }
  if ($('btn-colapsar-todos')) {
    $('btn-colapsar-todos').addEventListener('click', () => {
      document.querySelectorAll('#contenedor-acordeon-2027 .acordeon-partida').forEach(d => {
        d.open = false;
      });
    });
  }

  // Selector de ciclos gubernamentales
  document.querySelectorAll('.ciclo-tab[data-ciclo]').forEach(tab => {
    tab.addEventListener('click', () => {
      const ciclo = tab.dataset.ciclo;
      if (ciclo === '2026-2027') {
        document.querySelectorAll('.ciclo-tab').forEach(t => {
          t.classList.remove('activa');
          t.setAttribute('aria-selected', 'false');
        });
        tab.classList.add('activa');
        tab.setAttribute('aria-selected', 'true');
        cargarTermometro2027();
      } else {
        const msg = 'El ciclo ' + (ciclo === '2022-2023' ? '2022 → 2023 (Boric vs Piñera)' : '2018 → 2019 (Piñera vs Bachelet)') +
          ' es un archivo histórico referencial. El observatorio interactivo opera sobre el ciclo activo 2026 → 2027.';
        if ($('estado-2027')) $('estado-2027').textContent = msg;
      }
    });
  });
}

function iniciarChipsAtajos() {
  document.querySelectorAll('.chip-btn[data-termino], .chip-hero[data-termino]').forEach(btn => {
    btn.addEventListener('click', () => {
      const termino = btn.dataset.termino;
      activarVista('termometro', true);
      if ($('busqueda-2027')) {
        $('busqueda-2027').value = termino;
        document.querySelectorAll('.pill-btn[data-partida]').forEach(b => b.classList.toggle('activa', b.dataset.partida === ''));
        filtroPartida2027 = '';
        if ($('selector-partida-2027')) $('selector-partida-2027').value = '';
        cargarTermometro2027();
        const dest = $('comparador2027') || $('termometro');
        if (dest) dest.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
}

// -------------------------------------------------------------
// Matriz Comparativa de Articulado
// -------------------------------------------------------------
let filtroNivelArticulado = '';
let datosArticulado = [];

async function cargarMatrizArticulado() {
  const grid = $('articulado-grid');
  if (!grid) return;
  $('estado-articulado').textContent = 'Cargando comparación normativa y estado de fuentes…';

  try {
    const res = await obtener('/api/articulado');
    datosArticulado = Array.isArray(res) ? res : (res.ejes_comparativos || []);
    renderizarArticulado();
  } catch (e) {
    $('estado-articulado').textContent = 'Error al cargar la matriz de articulado.';
  }
}

function renderizarArticulado() {
  const grid = $('articulado-grid');
  if (!grid) return;
  grid.replaceChildren();

  const filtrados = filtroNivelArticulado
    ? datosArticulado.filter(item => item.categoria === filtroNivelArticulado)
    : datosArticulado;

  $('estado-articulado').textContent = `${filtrados.length} ejes normativos mostrados (${filtroNivelArticulado ? 'Filtro: ' + filtroNivelArticulado : 'Todos los ejes'}).`;

  for (const item of filtrados) {
    const card = elemento('article', undefined, 'art-card');

    const hdr = elemento('div', undefined, 'art-card-header');
    const titGroup = elemento('div');
    titGroup.append(
      elemento('div', item.eje, 'art-eje'),
      elemento('h3', `${item.icono || '📜'} ${item.articulo} · ${item.titulo}`)
    );

    let badgeClass = 'art-badge-moderado';
    if (item.nivel_cambio && item.nivel_cambio.includes('Crítico')) badgeClass = 'art-badge-critico';
    else if (item.nivel_cambio && item.nivel_cambio.includes('Mayor')) badgeClass = 'art-badge-mayor';
    const badge = elemento('span', `${item.categoria}: ${item.tipo_cambio}`, `badge ${badgeClass}`);
    hdr.append(titGroup, badge);

    const body = elemento('div', undefined, 'art-card-body');

    const col2026 = elemento('div', undefined, 'art-col');
    col2026.append(
      elemento('div', 'Ley 21.796 (2026) · ' + item.fuente_2026.articulo, 'art-col-title'),
      elemento('p', item.norma_2026, 'art-col-text')
    );

    const col2027 = elemento('div', undefined, 'art-col art-col-2027');
    col2027.append(
      elemento('div', 'Proyecto 2027 · copia local del Mensaje 180', 'art-col-title'),
      elemento('p', item.norma_2027, 'art-col-text')
    );

    body.append(col2026, col2027);

    const imp = elemento('div', undefined, 'art-card-impacto');
    const impStrong = elemento('strong', 'Alcance e implicancias: ');
    imp.append(impStrong, document.createTextNode(item.impacto_calle));

    const fuente = elemento('div', undefined, 'meta');
    const leyBtn = elemento('button', 'Fuente oficial 2026 · pág. ' + (item.fuente_2026.pagina || 'sin equivalente'), 'btn-mini-rec');
    leyBtn.style.padding = '.1rem .4rem';
    leyBtn.style.fontSize = '.75rem';
    leyBtn.addEventListener('click', () => {
      const url = item.fuente_2026.url + (item.fuente_2026.pagina ? '#page=' + item.fuente_2026.pagina : '');
      window.open(url, '_blank', 'noopener,noreferrer');
    });
    fuente.append(leyBtn, document.createTextNode(' · Proyecto local 2027, pág. ' + item.fuente_2027.pagina + ' · procedencia oficial pendiente.'));
    card.append(hdr, body, imp, fuente, elemento('p', item.limite, 'meta'));
    grid.append(card);
  }
}

function iniciarControlesArticulado() {
  document.querySelectorAll('.art-filtro[data-nivel]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.art-filtro[data-nivel]').forEach(b => b.classList.remove('activa'));
      btn.classList.add('activa');
      filtroNivelArticulado = btn.dataset.nivel;
      renderizarArticulado();
    });
  });
}

// -------------------------------------------------------------
// Radar Comisión Especial Mixta de Presupuestos
// -------------------------------------------------------------
async function cargarRadarMixta() {
  const contenedor = $('contenedor-hitos-mixta');
  if (!contenedor) return;

  if (!_cacheHitosMixta) {
    try {
      const dataMixta = await obtener('/api/comision-mixta');
      _cacheHitosMixta = dataMixta.hitos || [];
    } catch (e) {
      _cacheHitosMixta = [];
    }
  }

  const partidaFiltro = $('mixta-filtro-partida') ? $('mixta-filtro-partida').value : '';
  const estadoFiltro = $('mixta-filtro-estado') ? $('mixta-filtro-estado').value : '';
  const busq = $('mixta-busqueda') ? normalizarTexto($('mixta-busqueda').value) : '';

  let hitos = [...(_cacheHitosMixta || [])];
  if (partidaFiltro) hitos = hitos.filter(h => h.partida === partidaFiltro || h.partida === partidaFiltro.padStart(2, '0'));
  if (estadoFiltro) hitos = hitos.filter(h => h.estado === estadoFiltro);
  if (busq) {
    hitos = hitos.filter(h => {
      const bolsa = normalizarTexto([h.orador, h.cargo, h.tema_o_glosa, h.bajada_calle, h.partida_nombre, h.capitulo_nombre].join(' '));
      return bolsa.includes(busq);
    });
  }

  // Actualizar KPIs del Radar
  if ($('mixta-kpi-total')) $('mixta-kpi-total').textContent = (_cacheHitosMixta || []).length;
  if ($('mixta-kpi-rechazados')) {
    const rech = (_cacheHitosMixta || []).filter(h => h.estado.includes('Rechazado')).length;
    $('mixta-kpi-rechazados').textContent = rech;
  }
  if ($('mixta-kpi-protocolos')) {
    const prot = (_cacheHitosMixta || []).filter(h => h.estado.includes('Condicionada') || h.estado.includes('Protocolo')).length;
    $('mixta-kpi-protocolos').textContent = prot;
  }

  contenedor.replaceChildren();

  if (hitos.length === 0) {
    const emptyDiv = elemento('div', 'No se encontraron hitos parlamentarios con los filtros seleccionados.', 'meta');
    emptyDiv.style.padding = '2rem 1rem';
    emptyDiv.style.textAlign = 'center';
    contenedor.append(emptyDiv);
    return;
  }

  for (const h of hitos) {
    let claseEstado = 'hito-negociacion';
    if (h.estado.includes('Rechazado')) claseEstado = 'hito-rechazado';
    else if (h.estado.includes('Condicionada')) claseEstado = 'hito-condicionado';
    else if (h.estado.includes('Protocolo')) claseEstado = 'hito-protocolo';

    const card = elemento('article', undefined, `hito-card ${claseEstado}`);
    card.id = 'hito-' + h.id;

    const hdr = elemento('div', undefined, 'hito-card-header');
    hdr.append(
      elemento('span', `${h.fecha} · ${h.instancia}`, 'hito-meta'),
      elemento('span', h.estado, 'hito-badge-estado')
    );

    const cuerpo = elemento('div', undefined, 'hito-card-cuerpo');
    cuerpo.append(
      elemento('div', `Partida ${h.partida} ${h.partida_nombre} · ${h.capitulo_nombre}`, 'hito-cartera'),
      elemento('h3', h.tema_o_glosa, 'hito-titulo')
    );

    const oradorBox = elemento('div', undefined, 'hito-orador-box');
    oradorBox.append(
      elemento('span', '🎙️'),
      elemento('strong', h.orador),
      elemento('span', `(${h.cargo})`)
    );
    cuerpo.append(oradorBox);

    const dec = elemento('p', undefined, 'hito-decision');
    dec.append(elemento('strong', 'Resolución parlamentaria: '), document.createTextNode(h.postura_o_decision));
    cuerpo.append(dec);

    const calleBox = elemento('div', undefined, 'hito-bajada-calle-box');
    calleBox.append(
      elemento('strong', '🎯 Bajada a la Calle: '),
      document.createTextNode(h.bajada_calle)
    );
    cuerpo.append(calleBox);

    const footer = elemento('div', undefined, 'hito-card-footer');

    if (h.video_url_timestamp) {
      const btnVideo = elemento('button', '▶️ Ver debate en YouTube (minuto exacto)', 'btn-hito-accion btn-hito-video');
      btnVideo.title = 'Abrir video oficial del debate en YouTube en el minuto exacto';
      btnVideo.addEventListener('click', () => {
        window.open(h.video_url_timestamp, '_blank', 'noopener,noreferrer');
      });
      footer.append(btnVideo);
    }

    if (h.acta_url) {
      const btnActa = elemento('button', '📄 Ver Acta Oficial', 'btn-hito-accion');
      btnActa.title = 'Abrir tramitación oficial en el portal del Congreso';
      btnActa.addEventListener('click', () => {
        window.open(h.acta_url, '_blank', 'noopener,noreferrer');
      });
      footer.append(btnActa);
    }

    if (h.programa_codigo) {
      const btnProg = elemento('button', '🏛️ Ver programa en Observatorio', 'btn-hito-accion');
      btnProg.addEventListener('click', () => {
        activarVista('termometro', true);
        filtroPartida2027 = h.partida;
        if ($('selector-partida-2027')) $('selector-partida-2027').value = h.partida;
        poblarSelectorCapitulos(h.partida);
        cargarTermometro2027().then(() => {
          const fila = $('fila-prog-' + h.programa_codigo.replace(/[^a-zA-Z0-9_-]/g, '_'));
          if (fila) {
            fila.scrollIntoView({ behavior: 'smooth' });
            fila.classList.add('fila-destacada');
            setTimeout(() => fila.classList.remove('fila-destacada'), 2500);
          }
        });
      });
      footer.append(btnProg);
    }

    card.append(hdr, cuerpo, footer);
    contenedor.append(card);
  }
}

function iniciarControlesMixta() {
  if ($('mixta-filtro-partida')) {
    $('mixta-filtro-partida').addEventListener('change', cargarRadarMixta);
  }
  if ($('mixta-filtro-estado')) {
    $('mixta-filtro-estado').addEventListener('change', cargarRadarMixta);
  }
  if ($('mixta-busqueda')) {
    let t;
    $('mixta-busqueda').addEventListener('input', () => {
      clearTimeout(t);
      t = setTimeout(cargarRadarMixta, 200);
    });
  }
}

// -------------------------------------------------------------
// Modal de Novedades y Roadmap (DOM Seguro con createElement)
// -------------------------------------------------------------
const NOVEDADES_DATA = [
  {
    version: 'v1.2.2',
    estado: 'Vigente',
    claseBadge: 'vigente',
    vigente: true,
    titulo: 'Diseño Editorial evegat.cl, Neutralidad de 33 Partidas e Índice DIPRES',
    descripcion: 'Rediseño visual completo con tipografías Inter, Newsreader y Space Mono. Tablas numéricas fluidas sin descuadre, neutralidad absoluta de las 33 Partidas oficiales (con paridad total en Partida 27 Ministerio de la Mujer) e indexación masiva de 3.601 documentos oficiales DIPRES 2027.',
    hitos: [
      'Rediseño visual editorial: Fuentes Inter, Newsreader y Space Mono con paleta papel/bosque/terracota.',
      'Tablas numéricas fluidas: Ancho mínimo 880px, códigos en una sola línea y cifras tabulares con badges legibles.',
      'Neutralidad institucional: Acceso directo y paritario a las 33 Partidas oficiales íntegras.',
      'Digitalización DIPRES 2027: 3.601 documentos oficiales catalogados y disponibles para APIs y agentes (llms.txt, openapi.json).'
    ]
  },
  {
    version: 'v1.2.0',
    estado: 'Versión previa',
    claseBadge: 'hist',
    vigente: false,
    titulo: 'Observatorio de prioridades fiscales y su impacto en los habitantes de Chile',
    descripcion: 'Digitalización determinista de las 33 Partidas presupuestarias oficiales (515 programas) desde fuentes XML y CSV oficiales de DIPRES y Contraloría General de la República.',
    hitos: [
      'Digitalización y balance de 515 programas y 33 partidas del Proyecto de Presupuestos 2027.',
      'Selector de transiciones presidenciales con contraste macroeconómico ($217,89 billones brutos vs $105,8 billones gasto neto consolidado).',
      'Filtros multidimensionales por subtítulos oficiales DIPRES (Subtítulo 21 Personal, 22 Bienes, 24 Transferencias, 31 Inversión, etc.).',
      'Glosas pineadas de dotación máxima de personal y restricciones de contratación por servicio en drawer lateral.'
    ]
  },
  {
    version: 'v1.1.0',
    estado: 'Versión previa',
    claseBadge: 'hist',
    vigente: false,
    titulo: 'Ingesta de Seguridad, Obras Públicas y Justicia',
    descripcion: 'Expansión de coberturas sectoriales e incorporación de partidas clave para el análisis del gasto de capital y dotaciones operativas.',
    hitos: [
      'Ingesta y homologación de partidas de Interior, Seguridad Pública, Defensa, Obras Públicas y Justicia.',
      'Primeras equivalencias cívicas tangibles con catálogo de costos de compras públicas referenciales.'
    ]
  },
  {
    version: 'v1.0.0',
    estado: 'Versión inicial',
    claseBadge: 'hist',
    vigente: false,
    titulo: 'Prototipo Fundacional y Caso Cabildo',
    descripcion: 'Prototipo fundacional con 266 programas presupuestarios y caso de estudio en el territorio de Cabildo.',
    hitos: [
      'Relato en 4 actos: De la glosa presupuestaria al impacto concreto en la calle.',
      'Visualización interactiva mediante scrollytelling SVG sin rastreadores ni dependencias externas.'
    ]
  }
];

const ROADMAP_DATA = [
  {
    plazo: 'Q4 2026',
    estado: 'En desarrollo',
    claseBadge: 'dev',
    enDesarrollo: true,
    titulo: 'Archivos Históricos de Transición Presupuestaria',
    descripcion: 'Habilitación de los ciclos históricos de cambio de mando en el selector superior para contrastar alternancias de poder anteriores con el mismo nivel de detalle que el ciclo 2026 → 2027.',
    hitos: [
      'Ciclo 2022 → 2023: Comparativa presupuestaria histórica (digitalización de partidas y leyes correspondientes).',
      'Ciclo 2018 → 2019: Comparativa presupuestaria histórica (digitalización de partidas y leyes correspondientes).',
      'Comparador dinámico entre transiciones presidenciales históricas.'
    ]
  },
  {
    plazo: 'Q4 2026',
    estado: 'En desarrollo',
    claseBadge: 'dev',
    enDesarrollo: true,
    titulo: 'Debates Parlamentarios del Congreso',
    descripcion: 'Incorporación de fuentes audiovisuales y transcripciones estructuradas del debate presupuestario.',
    hitos: [
      'Sistematización de transmisiones de YouTube (TVSenado y Cámara de Diputadas y Diputados) del Presupuesto 2027.',
      'Pipeline de transcripciones, extracción de argumentos de parlamentarios y ministros vinculados a glosas e informes ejecutivos de posturas.'
    ]
  },
  {
    plazo: 'Q1 2027',
    estado: 'Planificado',
    claseBadge: 'plan',
    enDesarrollo: false,
    titulo: 'Trazabilidad de Contrataciones y Apertura Cívica',
    descripcion: 'Auditoría en tiempo real del gasto ejecutado y apertura de datos para investigación ciudadana.',
    hitos: [
      'Cruce de órdenes de compra reales de ChileCompra contra glosas presupuestarias aprobadas.',
      'API cívica abierta y descargas masivas en formatos abiertos para periodismo de datos e investigación.'
    ]
  }
];

function renderizarNovedades() {
  const panel = $('panel-novedades');
  if (!panel) return;
  panel.replaceChildren();

  for (const item of NOVEDADES_DATA) {
    const card = elemento('article', undefined, 'novedad-card' + (item.vigente ? ' vigente' : ''));
    const meta = elemento('div', undefined, 'card-meta');
    meta.append(
      elemento('strong', item.version, 'etiqueta'),
      elemento('span', item.estado, 'card-badge ' + item.claseBadge)
    );
    card.append(
      meta,
      elemento('h3', item.titulo, 'card-titulo'),
      elemento('p', item.descripcion, 'card-desc')
    );
    if (item.hitos && item.hitos.length) {
      const ul = elemento('ul', undefined, 'card-lista');
      for (const hito of item.hitos) ul.append(elemento('li', hito));
      card.append(ul);
    }
    panel.append(card);
  }
}

function renderizarRoadmap() {
  const panel = $('panel-roadmap');
  if (!panel) return;
  panel.replaceChildren();

  for (const item of ROADMAP_DATA) {
    const card = elemento('article', undefined, 'roadmap-card' + (item.enDesarrollo ? ' en-desarrollo' : ''));
    const meta = elemento('div', undefined, 'card-meta');
    meta.append(
      elemento('strong', item.plazo, 'etiqueta'),
      elemento('span', item.estado, 'card-badge ' + item.claseBadge)
    );
    card.append(
      meta,
      elemento('h3', item.titulo, 'card-titulo'),
      elemento('p', item.descripcion, 'card-desc')
    );
    if (item.hitos && item.hitos.length) {
      const ul = elemento('ul', undefined, 'card-lista');
      for (const hito of item.hitos) ul.append(elemento('li', hito));
      card.append(ul);
    }
    panel.append(card);
  }
}

function abrirModalNovedades(tabInicial) {
  const modal = $('modal-novedades');
  const backdrop = $('modal-novedades-backdrop');
  if (!modal || !backdrop) return;

  renderizarNovedades();
  renderizarRoadmap();

  if (tabInicial === 'roadmap') {
    activarTabModal('roadmap');
  } else {
    activarTabModal('novedades');
  }

  backdrop.classList.add('abierto');
  backdrop.setAttribute('aria-hidden', 'false');
  modal.classList.add('abierto');
  modal.setAttribute('aria-hidden', 'false');
  const btnCerrar = $('modal-novedades-cerrar');
  if (btnCerrar) btnCerrar.focus();
}

function cerrarModalNovedades() {
  const modal = $('modal-novedades');
  const backdrop = $('modal-novedades-backdrop');
  if (!modal || !backdrop) return;

  backdrop.classList.remove('abierto');
  backdrop.setAttribute('aria-hidden', 'true');
  modal.classList.remove('abierto');
  modal.setAttribute('aria-hidden', 'true');
  const btnTrigger = $('btn-novedades-roadmap');
  if (btnTrigger) btnTrigger.focus();
}

function activarTabModal(tab) {
  const btnNovedades = $('tab-novedades');
  const btnRoadmap = $('tab-roadmap');
  const panelNovedades = $('panel-novedades');
  const panelRoadmap = $('panel-roadmap');
  if (!btnNovedades || !btnRoadmap || !panelNovedades || !panelRoadmap) return;

  if (tab === 'roadmap') {
    btnNovedades.classList.remove('activa');
    btnNovedades.setAttribute('aria-selected', 'false');
    panelNovedades.classList.remove('activo');

    btnRoadmap.classList.add('activa');
    btnRoadmap.setAttribute('aria-selected', 'true');
    panelRoadmap.classList.add('activo');
  } else {
    btnRoadmap.classList.remove('activa');
    btnRoadmap.setAttribute('aria-selected', 'false');
    panelRoadmap.classList.remove('activo');

    btnNovedades.classList.add('activa');
    btnNovedades.setAttribute('aria-selected', 'true');
    panelNovedades.classList.add('activo');
  }
}

function iniciarModalNovedades() {
  const btnHeader = $('btn-novedades-roadmap');
  if (btnHeader) {
    btnHeader.addEventListener('click', () => abrirModalNovedades('novedades'));
  }
  const btnFooter = $('btn-footer-novedades');
  if (btnFooter) {
    btnFooter.addEventListener('click', () => abrirModalNovedades('novedades'));
  }
  const btnCerrar = $('modal-novedades-cerrar');
  if (btnCerrar) {
    btnCerrar.addEventListener('click', cerrarModalNovedades);
  }
  const backdrop = $('modal-novedades-backdrop');
  if (backdrop) {
    backdrop.addEventListener('click', cerrarModalNovedades);
  }
  const tabNov = $('tab-novedades');
  if (tabNov) {
    tabNov.addEventListener('click', () => activarTabModal('novedades'));
  }
  const tabRoad = $('tab-roadmap');
  if (tabRoad) {
    tabRoad.addEventListener('click', () => activarTabModal('roadmap'));
  }
  window.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape' || ev.key === 'Esc') {
      const modal = $('modal-novedades');
      if (modal && modal.classList.contains('abierto')) {
        cerrarModalNovedades();
      }
    }
  });
}

// -------------------------------------------------------------
// Inicialización General
// -------------------------------------------------------------
iniciarSuiteDifusion();
iniciarTabsSuperiores();
iniciarWidgetMacroDual();
servicios();
buscar();
comparar();
costos();
iniciarControles2027();
cargarTermometro2027();
iniciarChipsAtajos();
iniciarControlesArticulado();
cargarMatrizArticulado();
iniciarControlesMixta();
iniciarModalNovedades();
