
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
  recorridos: null
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
  "seguridad": ["seguridad publica", "carabineros", "policia", "orden publico", "crimen organizado", "lazos", "denuncia seguro"]
};

function normalizarTexto(txt) {
  return (txt || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
}

async function cargarJSONEstatico(nombre) {
  const r = await fetch('data/' + nombre, { headers: { Accept: 'application/json' } });
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}

async function resolverEstatico(url) {
  if (url.includes('/presupuesto2027')) {
    if (!_cacheEstatico.presupuesto2027) {
      _cacheEstatico.presupuesto2027 = await cargarJSONEstatico('presupuesto2027.json');
    }
    const full = _cacheEstatico.presupuesto2027;
    const urlObj = new URL(url, 'http://localhost');
    const partida = urlObj.searchParams.get('partida') || '';
    const q = urlObj.searchParams.get('q') || '';
    const orden = urlObj.searchParams.get('orden') || 'mayor_recorte';

    let progs = [...full.programas];
    if (partida) {
      progs = progs.filter(p => p.partida === partida || p.partida === partida.padStart(2, '0'));
    }
    if (q) {
      const qNorm = normalizarTexto(q);
      const tokens = qNorm.split(/\s+/).filter(Boolean);
      let terminos = [qNorm];
      for (const [alias, exp] of Object.entries(CIVIC_ALIASES)) {
        if (qNorm === alias || tokens.includes(alias)) {
          terminos = terminos.concat(exp.map(normalizarTexto));
        }
      }
      progs = progs.filter(p => {
        const bolsa = normalizarTexto([
          p.codigo, p.nombre_programa, p.nombre_capitulo, p.nombre_partida,
          p.bajada_calle ? (p.bajada_calle.impacto_texto + ' ' + p.bajada_calle.dilema) : ''
        ].join(' '));
        return terminos.some(t => bolsa.includes(t)) || tokens.every(tok => bolsa.includes(tok));
      });
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
      totales_mclp: full.totales_mclp,
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

async function abrirRecorrido(id) {
  $('drawer').classList.add('abierto');
  $('drawer-backdrop').classList.add('abierto');
  $('drawer').setAttribute('aria-hidden', 'false');
  $('recorrido-titulo').textContent = 'Cargando recorrido…';
  $('recorrido-descripcion').textContent = '…';
  $('recorrido-estaciones').replaceChildren();
  try {
    const data = await obtener('/api/recorrido/' + encodeURIComponent(id));
    const p = data.programa;
    $('recorrido-servicio').textContent = p.servicio || p.ministerio || 'Servicio Público';
    $('recorrido-titulo').textContent = p.nombre_programa;
    $('recorrido-presupuesto').textContent = 'Presupuesto 2026: ' + numero(p.presupuesto_2026_m$) + ' M$ (' + (p.variacion_pct ? p.variacion_pct + '%' : 'sin variación declarada') + ')';
    $('recorrido-descripcion').textContent = p.descripcion || 'Sin descripción oficial en BIPS.';
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

// Termómetro Presupuesto 2027 vs 2026
let filtroPartida2027 = '';
let orden2027 = 'mayor_recorte';

async function cargarTermometro2027() {
  const tablaBody = $('tabla-2027-body');
  if (!tablaBody) return;
  tablaBody.replaceChildren();
  $('estado-2027').textContent = 'Cargando datos presupuestarios oficiales 2027…';

  const params = new URLSearchParams();
  if (filtroPartida2027) params.set('partida', filtroPartida2027);
  if (orden2027) params.set('orden', orden2027);
  const busq = $('busqueda-2027') ? $('busqueda-2027').value.trim() : '';
  if (busq) params.set('q', busq);

  try {
    const res = await obtener('/api/presupuesto2027?' + params);
    $('estado-2027').textContent = res.total_programas + ' programas analizados (' + (filtroPartida2027 ? 'Partida ' + filtroPartida2027 : 'Todas las partidas') + ').';

    if (!busq && $('kpi-total-proy')) {
      $('kpi-total-proy').textContent = '$' + numero(Math.round(res.totales_mclp.proyecto_2027 / 1000)) + 'B';
      const difIni = res.totales_mclp.dif_vs_ini;
      const pctIni = (res.totales_mclp.proyecto_2027 / res.totales_mclp.inicial_2026 - 1) * 100;
      $('kpi-var-ini').textContent = (difIni >= 0 ? '+' : '') + '$' + numero(Math.round(difIni / 1000)) + 'B (' + (pctIni >= 0 ? '+' : '') + pctIni.toFixed(1) + '%)';
      $('kpi-var-ini').className = 'badge ' + (difIni >= 0 ? 'badge-sube' : 'badge-baja');
    }

    for (const p of res.programas) {
      const tr = elemento('tr');

      const tdCod = elemento('td', p.codigo, 'meta');
      const tdProg = elemento('td');
      tdProg.append(elemento('strong', p.nombre_programa));
      tdProg.append(elemento('div', p.nombre_capitulo + ' · ' + p.nombre_partida, 'meta'));
      if (p.bajada_calle) {
        const b = elemento('div', p.bajada_calle.icono + ' ' + p.bajada_calle.impacto_texto, 'badge-calle ' + (p.bajada_calle.signo === '+' ? 'calle-sube' : 'calle-baja'));
        b.title = 'Equivalencia física: ' + p.bajada_calle.impacto_texto + ' (Ref: $' + numero(p.bajada_calle.costo_unitario_ref) + ')';
        tdProg.append(b);
      }

      const tdIni = elemento('td', '$' + numero(p.ini_2026_mclp), 'num');
      const tdVig = elemento('td', '$' + numero(p.vig_2026_mclp), 'num');
      const tdProy = elemento('td', '$' + numero(p.proy_2027_mclp), 'num');

      const tdDifIni = elemento('td', undefined, 'num');
      if (p.pct_vs_ini !== null) {
        const span = elemento('span', (p.dif_vs_ini_mclp >= 0 ? '+' : '') + '$' + numero(p.dif_vs_ini_mclp) + ' (' + (p.pct_vs_ini >= 0 ? '+' : '') + p.pct_vs_ini.toFixed(1) + '%)');
        span.className = p.dif_vs_ini_mclp >= 0 ? 'var-pos' : 'var-neg';
        tdDifIni.append(span);
      } else {
        tdDifIni.textContent = 'Nuevo en 2027';
      }

      const tdDifVig = elemento('td', undefined, 'num');
      if (p.pct_vs_vig !== null) {
        const span = elemento('span', (p.dif_vs_vig_mclp >= 0 ? '+' : '') + '$' + numero(p.dif_vs_vig_mclp) + ' (' + (p.pct_vs_vig >= 0 ? '+' : '') + p.pct_vs_vig.toFixed(1) + '%)');
        span.className = p.dif_vs_vig_mclp >= 0 ? 'var-pos' : 'var-neg';
        tdDifVig.append(span);
      } else {
        tdDifVig.textContent = 'Nuevo en 2027';
      }

      const tdAccion = elemento('td', undefined, 'num');
      const btn = elemento('button', 'Recorrido →', 'btn-mini-rec');
      btn.addEventListener('click', () => abrirRecorrido(p.codigo || p.nombre_programa));
      tdAccion.append(btn);

      tr.append(tdCod, tdProg, tdIni, tdVig, tdProy, tdDifIni, tdDifVig, tdAccion);
      tablaBody.append(tr);
    }
  } catch (e) {
    $('estado-2027').textContent = 'Error al consultar la comparativa presupuestaria 2027.';
  }
}

function iniciarControles2027() {
  document.querySelectorAll('.pill-btn[data-partida]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.pill-btn[data-partida]').forEach(b => b.classList.remove('activa'));
      btn.classList.add('activa');
      filtroPartida2027 = btn.dataset.partida;
      cargarTermometro2027();
    });
  });

  if ($('orden-2027')) {
    $('orden-2027').addEventListener('change', e => {
      orden2027 = e.target.value;
      cargarTermometro2027();
    });
  }

  if ($('busqueda-2027')) {
    let t;
    $('busqueda-2027').addEventListener('input', () => {
      clearTimeout(t);
      t = setTimeout(cargarTermometro2027, 250);
    });
  }
}

function iniciarChipsAtajos() {
  document.querySelectorAll('.chip-btn[data-termino], .chip-hero[data-termino]').forEach(btn => {
    btn.addEventListener('click', () => {
      const termino = btn.dataset.termino;
      if ($('busqueda-2027')) {
        $('busqueda-2027').value = termino;
        document.querySelectorAll('.pill-btn[data-partida]').forEach(b => b.classList.toggle('activa', b.dataset.partida === ''));
        filtroPartida2027 = '';
        cargarTermometro2027();
        const dest = $('comparador2027') || $('termometro-2027');
        if (dest) dest.scrollIntoView({ behavior: 'smooth' });
      } else if ($('busqueda')) {
        $('busqueda').value = termino;
        buscar();
        $('evidencia').scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
}

servicios(); buscar(); comparar(); costos();
iniciarControles2027();
cargarTermometro2027();
iniciarChipsAtajos();

// Matriz Comparativa de Articulado
let filtroNivelArticulado = '';
let datosArticulado = [];

async function cargarMatrizArticulado() {
  const grid = $('articulado-grid');
  if (!grid) return;
  $('estado-articulado').textContent = 'Cargando articulado oficial 2026 vs 2027…';

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
    ? datosArticulado.filter(item => item.nivel_cambio && item.nivel_cambio.toLowerCase().includes(filtroNivelArticulado.toLowerCase()))
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
    const badge = elemento('span', `${item.nivel_cambio}: ${item.tipo_cambio}`, `badge ${badgeClass}`);
    hdr.append(titGroup, badge);

    const body = elemento('div', undefined, 'art-card-body');

    const col2026 = elemento('div', undefined, 'art-col');
    col2026.append(
      elemento('div', 'Ley 2026 (Vigente)', 'art-col-title'),
      elemento('p', item.norma_2026, 'art-col-text')
    );

    const col2027 = elemento('div', undefined, 'art-col art-col-2027');
    col2027.append(
      elemento('div', 'Proyecto 2027 (Mensaje N° 180)', 'art-col-title'),
      elemento('p', item.norma_2027, 'art-col-text')
    );

    body.append(col2026, col2027);

    const imp = elemento('div', undefined, 'art-card-impacto');
    const impStrong = elemento('strong', 'Impacto Cívico y en la Calle: ');
    imp.append(impStrong, document.createTextNode(item.impacto_calle));

    card.append(hdr, body, imp);
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

iniciarControlesArticulado();
cargarMatrizArticulado();
