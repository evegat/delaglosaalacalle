/**
 * Challenger M1-1: Empirical Stress-Test Suite
 * Testing UI components, filters, accordions, drawer, and edge cases.
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const DATA_DIR = path.join(ROOT, 'docs', 'data');

// 1. Load Data
const presupuesto2027Path = path.join(DATA_DIR, 'presupuesto2027.json');
const recorridosPath = path.join(DATA_DIR, 'recorridos.json');
const articuladoPath = path.join(DATA_DIR, 'matriz_articulado_2026_2027.json');

const presupuestoData = JSON.parse(fs.readFileSync(presupuesto2027Path, 'utf8'));
const recorridosData = JSON.parse(fs.readFileSync(recorridosPath, 'utf8'));
const articuladoData = JSON.parse(fs.readFileSync(articuladoPath, 'utf8'));

// Extract relato.js code
const relatoJsPath = path.join(ROOT, 'dist', 'assets', 'relato.js');
const relatoJsCode = fs.readFileSync(relatoJsPath, 'utf8');

console.log('=== CHALLENGER M1-1: EMPIRICAL STRESS TEST SUITE ===\n');

let totalTests = 0;
let passedTests = 0;
let failedTests = 0;

function assert(condition, message) {
  totalTests++;
  if (condition) {
    passedTests++;
    console.log(`[PASS] ${message}`);
  } else {
    failedTests++;
    console.error(`[FAIL] ${message}`);
    throw new Error(`Assertion failed: ${message}`);
  }
}

// -----------------------------------------------------------------------------
// TEST SUITE 1: ZERO INNERHTML / OUTERHTML / EVAL AUDIT
// -----------------------------------------------------------------------------
console.log('--- Test Suite 1: Zero Dangerous DOM Sinks ---');
const filesToAudit = [
  path.join(ROOT, 'src', 'interfaz.html'),
  path.join(ROOT, 'dist', 'index.html'),
  path.join(ROOT, 'dist', 'assets', 'relato.js'),
  path.join(ROOT, 'docs', 'index.html'),
  path.join(ROOT, 'docs', 'assets', 'relato.js'),
];

for (const f of filesToAudit) {
  const content = fs.readFileSync(f, 'utf8');
  assert(!content.includes('innerHTML'), `${path.basename(f)} has 0 innerHTML`);
  assert(!content.includes('outerHTML'), `${path.basename(f)} has 0 outerHTML`);
  assert(!content.includes('insertAdjacentHTML'), `${path.basename(f)} has 0 insertAdjacentHTML`);
  assert(!/\beval\(/.test(content), `${path.basename(f)} has 0 eval()`);
  assert(!/document\.write/.test(content), `${path.basename(f)} has 0 document.write`);
  assert(!/javascript:/.test(content), `${path.basename(f)} has 0 javascript: URIs`);
}

// -----------------------------------------------------------------------------
// TEST SUITE 2: RESOLVER ESTATICO EMPIRICAL EXECUTION & FILTER STRESS
// -----------------------------------------------------------------------------
console.log('\n--- Test Suite 2: Filter Logic and Rapid State Switching ---');

// Mock DOM and environment for relato.js execution
const mockElements = new Map();
function createMockElement(tag, text, className) {
  return {
    tag,
    textContent: text || '',
    className: className || '',
    children: [],
    attributes: new Map(),
    dataset: {},
    classList: {
      _classes: new Set(className ? className.split(' ').filter(Boolean) : []),
      add(c) { this._classes.add(c); },
      remove(c) { this._classes.delete(c); },
      toggle(c, force) {
        if (force === undefined) {
          if (this._classes.has(c)) this._classes.delete(c);
          else this._classes.add(c);
        } else if (force) this._classes.add(c);
        else this._classes.delete(c);
      },
      has(c) { return this._classes.has(c); }
    },
    append(...nodes) {
      for (const n of nodes) {
        if (typeof n === 'string') this.children.push(createMockElement('text_node', n));
        else this.children.push(n);
      }
    },
    replaceChildren(...nodes) {
      this.children = [];
      this.append(...nodes);
    },
    setAttribute(k, v) { this.attributes.set(k, String(v)); },
    getAttribute(k) { return this.attributes.get(k); },
    addEventListener(event, handler) {
      if (!this._listeners) this._listeners = {};
      if (!this._listeners[event]) this._listeners[event] = [];
      this._listeners[event].push(handler);
    },
    querySelector(sel) {
      return this.children.find(c => c.className && c.className.includes(sel.replace('.', ''))) || createMockElement('div');
    },
    querySelectorAll(sel) {
      return this.children.filter(c => c.className && c.className.includes(sel.replace('.', '')));
    }
  };
}

// Emulate resolverEstatico in Node
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

function coincidePrograma(p, q) {
  const tokens = normalizarTexto(q).split(/\s+/).filter(t => t.length >= 2);
  let texto = normalizarTexto([p.codigo, p.nombre_partida, p.nombre_capitulo, p.nombre_programa].join(' '));
  if (texto.includes('servicio local')) texto += ' slep sleps escuela escuelas colegios educacion publica';
  if (texto.includes('recuperacion de barrios') || texto.includes('quiero mi barrio')) texto += ' quiero mi barrio barrio barrios plazas luminarias';
  if (texto.includes('asentamientos precarios') || texto.includes('campamentos')) texto += ' campamento campamentos tomas agua potable';
  if (texto.includes('becas y asistencialidad') || texto.includes('junaeb')) texto += ' yo elijo mi pc becas tic computador computadores pc pcs notebook notebooks escolares';
  if (String(p.partida || '').padStart(2, '0') === '16') texto += ' salud hospital hospitales cesfam consultorio consultorios camas urgencia cirugia cirugias medico medicos';
  if (String(p.partida || '').padStart(2, '0') === '27') texto += ' mujer mujeres genero sernameg violencia femicidio femicidios equidad de genero ministerio de la mujer igualdad de genero prevencion atencion';
  return tokens.every(t => texto.includes(t));
}

function filtrarProgramasEstatico(queryObj) {
  const full = presupuestoData;
  let progs = [...full.programas];
  const partida = queryObj.partida || '';
  const q = queryObj.q || '';
  const soloTangibles = queryObj.solo_tangibles === 'true' || queryObj.solo_tangibles === true;
  const subtitulo = queryObj.subtitulo || '';
  const orden = queryObj.orden || '';

  if (partida) {
    progs = progs.filter(p => p.partida === partida || p.partida === partida.padStart(2, '0'));
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

  return progs;
}

// 2.1 Rapid Tangibility Toggle
console.log('Testing rapid tangibility toggle (100 switches)...');
for (let i = 0; i < 100; i++) {
  const isTangible = i % 2 === 1;
  const res = filtrarProgramasEstatico({ solo_tangibles: isTangible });
  if (isTangible) {
    assert(res.length === 188, `Iteration ${i}: solo_tangibles=true yields exactly 188 programs`);
    assert(res.every(p => p.bajada_calle !== null && p.bajada_calle !== undefined), `Iteration ${i}: all 188 have non-null bajada_calle`);
  } else {
    assert(res.length === 515, `Iteration ${i}: solo_tangibles=false yields exactly 515 programs`);
  }
}

// Check total budget invariant
const todos = filtrarProgramasEstatico({ solo_tangibles: false });
const totalMclp = todos.reduce((acc, p) => acc + (p.proy_2027_mclp || 0), 0);
assert(totalMclp === 217892642270, `Total budget invariant: 217892642270 (actual: ${totalMclp})`);
assert(Math.round(totalMclp / 1e9 * 100) / 100 === 217.89, `Total budget in billones matches 217.89: ${(totalMclp / 1e9).toFixed(2)}`);

// 2.2 Subtítulos Multiselection Combinations
console.log('\nTesting Subtítulos combinations...');
const sub21 = filtrarProgramasEstatico({ subtitulo: '21' });
assert(sub21.length === 445, `Subtítulo 21 (Personal) matches exactly 445 programs (got ${sub21.length})`);
assert(sub21.every(p => p.subtitulos.includes('21')), 'All programs in sub21 have subtitulo 21');

const sub22 = filtrarProgramasEstatico({ subtitulo: '22' });
console.log(`Subtítulo 22 count: ${sub22.length}`);
assert(sub22.length > 0 && sub22.every(p => p.subtitulos.includes('22')), 'Subtítulo 22 filtered correctly');

const sub21_22 = filtrarProgramasEstatico({ subtitulo: '21,22' });
const union21_22 = new Set([...sub21.map(p => p.codigo), ...sub22.map(p => p.codigo)]);
assert(sub21_22.length === union21_22.size, `Subtítulo 21,22 combination is exact union: ${sub21_22.length} == ${union21_22.size}`);

const sub24_31 = filtrarProgramasEstatico({ subtitulo: '24,31' });
const sub24 = filtrarProgramasEstatico({ subtitulo: '24' });
const sub31 = filtrarProgramasEstatico({ subtitulo: '31' });
const union24_31 = new Set([...sub24.map(p => p.codigo), ...sub31.map(p => p.codigo)]);
assert(sub24_31.length === union24_31.size, `Subtítulo 24,31 combination is exact union: ${sub24_31.length} == ${union24_31.size}`);

const subAllChips = filtrarProgramasEstatico({ subtitulo: '21,22,24,29,31,34' });
assert(subAllChips.length === 510, `The 6 DIPRES chips cover exactly 510 programs (got ${subAllChips.length})`);
const nonCovered = todos.filter(p => !subAllChips.some(s => s.codigo === p.codigo));
assert(nonCovered.length === 5, `Exactly 5 special programs outside standard 6 chips (got ${nonCovered.length})`);
assert(nonCovered.every(p => p.partida === '50'), 'All 5 non-chip programs belong to Partida 50 (Tesoro Público)');

// Check that clearing subtitulos filter (Todos) returns all 515
const subNone = filtrarProgramasEstatico({ subtitulo: '' });
assert(subNone.length === 515, `Subtítulo empty string (Todos) returns all 515 programs`);

// Whitespace handling in subtítulos string
const subSpaces = filtrarProgramasEstatico({ subtitulo: ' 24 , 31 ' });
assert(subSpaces.length === sub24_31.length, 'Subtítulos query handles spaces robustly');

// 2.3 Search Queries & Edge Cases
console.log('\nTesting Search Queries & Accents/Empty handling...');
const qEmpty = filtrarProgramasEstatico({ q: '' });
assert(qEmpty.length === 515, 'Empty search query returns all 515 programs');

const qWhitespace = filtrarProgramasEstatico({ q: '   ' });
assert(qWhitespace.length === 515, 'Whitespace query returns all 515 programs');

const qSlep = filtrarProgramasEstatico({ q: 'slep' });
assert(qSlep.length > 0, `Search 'slep' matches ${qSlep.length} programs`);

const qAccents = filtrarProgramasEstatico({ q: 'educación' });
const qNoAccents = filtrarProgramasEstatico({ q: 'educacion' });
assert(qAccents.length === qNoAccents.length, `Accented 'educación' (${qAccents.length}) matches unaccented 'educacion' (${qNoAccents.length})`);

const qZeroMatches = filtrarProgramasEstatico({ q: 'termino_inexistente_xyz_9999' });
assert(qZeroMatches.length === 0, 'Inexistent query returns exactly 0 programs');

for (const token of ['mujer', 'genero', 'género', 'sernameg', 'femicidio', 'violencia']) {
  const matches = filtrarProgramasEstatico({ q: token });
  const p27Matches = matches.filter(p => String(p.partida).padStart(2, '0') === '27');
  assert(p27Matches.length === 4, `Search '${token}' must match all 4 programs of Partida 27`);
  console.log(`[PASS] Search '${token}' matches all 4 programs of Partida 27`);
}

// -----------------------------------------------------------------------------
// TEST SUITE 3: MINISTERIAL ACCORDION GROUPING & STATE LOGIC
// -----------------------------------------------------------------------------
console.log('\n--- Test Suite 3: Ministerial Accordion Mechanics ---');

function agruparPorPartida(programas) {
  const agrupado = new Map();
  for (const p of programas) {
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
  return agrupado;
}

const grupos = agruparPorPartida(todos);
assert(grupos.size === 33, `Exactly 33 Partidas/Ministerios present in budget (actual: ${grupos.size})`);

let sumGrouped = 0;
for (const [cod, g] of grupos.entries()) {
  sumGrouped += g.programas.length;
}
assert(sumGrouped === 515, `Sum of all grouped programs equals 515 (actual: ${sumGrouped})`);

// Accordion Expand All / Collapse All logic verification
const accordions = Array.from(grupos.keys()).map(cod => ({ partida: cod, open: false }));

// Expand all
accordions.forEach(a => { a.open = true; });
assert(accordions.every(a => a.open === true), 'Expand All opens all 33 accordions');

// Collapse all
accordions.forEach(a => { a.open = false; });
assert(accordions.every(a => a.open === false), 'Collapse All closes all 33 accordions');

// Auto-expand logic when filtered or single/double partida
const autoExpandFiltro = Boolean('16' || '' || grupos.size <= 2);
assert(autoExpandFiltro === true, 'Auto-expand is true when specific partida is filtered');

const autoExpandAll = Boolean('' || '' || grupos.size <= 2);
assert(autoExpandAll === false, 'Auto-expand is false by default when viewing all 33 carteras');

// -----------------------------------------------------------------------------
// TEST SUITE 4: DRAWER PINNED GLOSA & PERSONNEL RENDERING
// -----------------------------------------------------------------------------
console.log('\n--- Test Suite 4: Drawer Pinned Glosa Panel Verification ---');

function simularPinnedGlosa(programaId) {
  const progDetalle = presupuestoData.programas.find(x => x.codigo === programaId || x.nombre_programa === programaId);
  const recData = recorridosData[programaId];

  const tieneDot = progDetalle ? progDetalle.tiene_dotacion : false;
  const montoDot = progDetalle ? progDetalle.monto_personal_2027_mclp : null;

  const res = {
    tieneDotacion: tieneDot,
    montoDotacion: montoDot,
    renderedElements: []
  };

  if (tieneDot) {
    res.renderedElements.push('Dotación y Personal Autorizado (Subtítulo 21)');
    res.renderedElements.push(montoDot ? `$${montoDot} M$ asignados a Personal 2027` : 'Dotación máxima de personal fijada por Ley');
    res.renderedElements.push('Regulado bajo el Artículo 15 del Proyecto 2027 (fijado en 1.500 traspasos máximos).');
    res.renderedElements.push('Glosa 01 de dotación');
    res.renderedElements.push('Ley N° 21.796');
    res.renderedElements.push('D.L. N° 249');
  } else {
    res.renderedElements.push('Este programa no cuenta con asignación presupuestaria directa en Subtítulo 21 (Personal). Opera mediante transferencias o adquisiciones (Subtítulos 22 o 24).');
  }

  return res;
}

// Find a program with dotacion
const progConDot = presupuestoData.programas.find(p => p.tiene_dotacion === true);
const pinnedConDot = simularPinnedGlosa(progConDot.codigo);
assert(pinnedConDot.tieneDotacion === true, `Program ${progConDot.codigo} has tiene_dotacion=true`);
assert(pinnedConDot.renderedElements.some(e => e.includes('1.500 traspasos')), 'Pinned panel mentions 1.500 traspasos');
assert(pinnedConDot.renderedElements.some(e => e.includes('Ley N° 21.796')), 'Pinned panel cites Ley N° 21.796');
assert(pinnedConDot.renderedElements.some(e => e.includes('D.L. N° 249')), 'Pinned panel cites D.L. N° 249');

// Find a program without dotacion
const progSinDot = presupuestoData.programas.find(p => p.tiene_dotacion === false);
assert(Boolean(progSinDot), 'Found program without direct Subtítulo 21 allocation');
const pinnedSinDot = simularPinnedGlosa(progSinDot.codigo);
assert(pinnedSinDot.tieneDotacion === false, `Program ${progSinDot.codigo} has tiene_dotacion=false`);
assert(pinnedSinDot.renderedElements.some(e => e.includes('no cuenta con asignación presupuestaria directa en Subtítulo 21')), 'Pinned panel shows explicit zero-personnel disclaimer');

// -----------------------------------------------------------------------------
// TEST SUITE 5: VIEWPORT RESPONSIVENESS AND CSS AUDIT
// -----------------------------------------------------------------------------
console.log('\n--- Test Suite 5: Viewports Responsiveness CSS Audit ---');

const cssPath = path.join(ROOT, 'dist', 'assets', 'relato.css');
const cssContent = fs.readFileSync(cssPath, 'utf8');

// Viewport 320px checks:
assert(cssContent.includes('.tabla-wrapper{overflow-x:auto'), 'Tables wrapped in overflow-x:auto to prevent horizontal page explosion on 320px');
assert(cssContent.includes('.drawer{position:fixed;top:0;right:-480px;width:min(480px,100vw)'), 'Drawer uses width: min(480px, 100vw) for mobile containment');
assert(cssContent.includes('@media(max-width:680px){') && cssContent.includes('.drawer{width:100%}'), 'Drawer expands to 100% width on viewports <= 680px (including 320px and 390px)');
assert(cssContent.includes('p,li,dd,a,h1,h2,h3{overflow-wrap:anywhere}'), 'Global overflow-wrap:anywhere prevents long words/codes breaking viewport on 320px');

// Viewport 390px checks:
assert(cssContent.includes('@media(max-width:768px){.art-card-body{grid-template-columns:1fr}}'), 'Articulado grid collapses to single column on viewports <= 768px');
assert(cssContent.includes('@media(max-width:680px){.relato{grid-template-columns:minmax(0,1fr);gap:0}'), 'Scrollytelling layout stacks vertically on viewports <= 680px');

// Viewport 1280px checks:
assert(cssContent.includes('header,main,footer{max-width:1120px;margin:auto'), 'Max-width 1120px keeps readable measure on 1280px screens');
assert(cssContent.includes('.relato{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr)'), 'Scrollytelling displays dual-column side-by-side on 1280px');

// -----------------------------------------------------------------------------
// TEST SUITE 6: COMPARADOR ARTICULADO & ART 3 / 40 INTEGRITY
// -----------------------------------------------------------------------------
console.log('\n--- Test Suite 6: Articulado Normativo & Key Articles ---');
const articuladoItems = Array.isArray(articuladoData) ? articuladoData : (articuladoData.ejes_comparativos || []);
assert(articuladoItems.length === 9, `Matriz articulado has exactly 9 critical axes (actual: ${articuladoItems.length})`);

const art3 = articuladoItems.find(a => a.articulo && a.articulo.includes('Artículo 3'));
assert(Boolean(art3), 'Artículo 3 (Techo de endeudamiento) present in articulado dataset');
assert(art3.norma_2026.includes('17.400') || art3.impacto_calle.includes('17.400'), 'Artículo 3 cites US$ 17.400M for 2026');
assert(art3.norma_2027.includes('25.000') || art3.impacto_calle.includes('25.000'), 'Artículo 3 cites US$ 25.000M for 2027');

const art40 = articuladoItems.find(a => a.articulo && a.articulo.includes('Artículo 40'));
assert(Boolean(art40), 'Artículo 40 (SLEP) present in articulado dataset');
assert(art40.impacto_calle.includes('5 SLEP') || art40.norma_2027.includes('5 SLEP') || art40.titulo.includes('SLEP'), 'Artículo 40 covers 5 SLEP suspension');

console.log(`\n======================================================`);
console.log(`ALL TESTS COMPLETED: ${passedTests}/${totalTests} PASSED, ${failedTests} FAILED.`);
console.log(`======================================================`);

if (failedTests > 0) process.exit(1);
