const fs = require('fs');
const assert = require('assert');

// 1. CNAME check
const cnameDist = fs.readFileSync('dist/CNAME', 'utf8').trim();
const cnameDocs = fs.readFileSync('docs/CNAME', 'utf8').trim();
assert.strictEqual(cnameDist, 'delaglosaalacalle.evegat.cl', 'dist/CNAME must match canonical domain');
assert.strictEqual(cnameDocs, 'delaglosaalacalle.evegat.cl', 'docs/CNAME must match canonical domain');
console.log('[PASS] CNAME files verified');

// 2. HTML audit
for (const f of ['dist/index.html', 'docs/index.html', 'src/interfaz.html']) {
  const content = fs.readFileSync(f, 'utf8');
  assert(!content.includes('data-cartera'), `${f} must have 0 discriminatory data-cartera cards`);
  assert(!content.includes('data-partida="16"'), `${f} must not have discriminatory pill for partida 16`);
  assert(!content.includes('data-partida="09"'), `${f} must not have discriminatory pill for partida 09`);
  assert(!content.includes('data-partida="27"'), `${f} must not have discriminatory pill for partida 27`);
  assert(content.includes('data-partida=""'), `${f} must have neutral reset pill`);
  assert(content.includes('Partida 27 · Ministerio de la Mujer y la Equidad de Género'), `${f} must include Partida 27 in selector`);

  const partidasCount = (content.match(/<option value="[0-9]{2}">Partida/g) || []).length;
  assert.strictEqual(partidasCount, 33, `${f} must contain exactly 33 partidas in selector`);
}
console.log('[PASS] HTML neutrality and 33 partidas verified');

// 3. JS financial formatting audit
for (const f of ['dist/assets/relato.js', 'docs/assets/relato.js']) {
  const content = fs.readFileSync(f, 'utf8');
  assert(content.includes('formatearVarBadge'), `${f} must use formatearVarBadge helper`);
  assert(!content.includes("'+$' + numero(p.dif_vs_ini_mclp)"), `${f} must not have broken sign logic`);
  assert(content.includes("signClp + numero(Math.abs(dif))"), `${f} must handle sign before currency symbol`);
  assert(content.includes("minimumFractionDigits: 1"), `${f} must format percentage with es-CL locale`);
}
console.log('[PASS] Financial badge formatting verified');

// 4. CSS typography & table layout audit
for (const f of ['dist/assets/relato.css', 'docs/assets/relato.css']) {
  const css = fs.readFileSync(f, 'utf8');
  assert(css.includes("'Inter',system-ui"), `${f} must declare Inter for body text`);
  assert(css.includes("'Newsreader',Georgia,serif"), `${f} must declare Newsreader for editorial titles`);
  assert(css.includes("'Space Mono',monospace"), `${f} must declare Space Mono for data & codes`);
  assert(css.includes('.th-accion') && css.includes('.td-accion'), `${f} must style table action columns`);
  assert(css.includes('.th-monto') && css.includes('.td-monto'), `${f} must style table numeric monetary columns`);
  assert(css.includes('--paper:#f7f5ef'), `${f} must define canonical paper token`);
  assert(css.includes('--ink:#13201e'), `${f} must define canonical ink token`);
  assert(css.includes('--deep:#0a2f2b'), `${f} must define canonical deep token`);
  assert(css.includes('--accent:#d7653b'), `${f} must define canonical accent token`);
  assert(css.includes('--line:#ccd7d2'), `${f} must define canonical line token`);
  assert(css.includes('--soft:#e9efec'), `${f} must define canonical soft token`);
}
console.log('[PASS] Editorial typography & table layout verified');

console.log('\n=== ALL REVIEWER AUDIT CHECKS PASSED ===');
