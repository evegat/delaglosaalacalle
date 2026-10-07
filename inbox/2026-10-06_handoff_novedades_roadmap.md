# Handoff: P149 — Incorporación de Modal de Novedades y Roadmap (YouTube Q4)

**Fecha:** 2026-10-06 20:56 CLT  
**Rama Git:** `EduCodex/p149-propuesta-valor-p01-20261006`  
**Último Commit:** `c06a2e6` (Working tree limpio, 120/120 tests PASS, 0 hallazgos security/quality)  
**Directorio de trabajo:** `c:\Users\evega\OneDrive\Documents\Obsidian\MyWorld\2 - Project\P149 - De la Glosa a la Calle\deploy`

---

## 1. Contexto y Estado Actual
- **Hito cerrado previo:** Digitalización determinista de las 33 Partidas oficiales (515 programas) desde XML/CSV de DIPRES/Contraloría, selector de transiciones presidenciales, filtros por subtítulos oficiales y glosas pineadas de personal. Verificado bajo arnés MyWorld y evaluado por auditor independiente con **VICTORY CONFIRMED**.
- **Nuevo requerimiento acordado con Eduardo:**
  1. Equiparar la interfaz al estándar de `ordenanzas.evegat.cl` incorporando un botón en cabecera/footer tipo badge (`v1.2.0 · Novedades & Roadmap 🎁` o similar).
  2. Al cliquear, despliega un modal liviano en Vanilla JS (cero dependencias, seguro contra XSS, sin `innerHTML`).
  3. **Pestaña 1 - Novedades (Changelog):**
     - **v1.2.0 (Vigente):** Observatorio de Prioridades Fiscales y Cambio de Gobierno (515 programas, 33 partidas, filtros multidimensionales, glosas de dotación).
     - **v1.1.0:** Ingesta de Seguridad, Obras Públicas y Justicia.
     - **v1.0.0:** Prototipo fundacional de 266 programas y caso Cabildo.
  4. **Pestaña 2 - Roadmap (Hoja de Ruta Pública):**
     - **Q4 2026 (En desarrollo):**
       - **Debates del Congreso:** Sistematización de transmisiones de YouTube (TVSenado y Cámara) del Presupuesto 2027: pipeline de transcripciones, extracción de argumentos de parlamentarios/ministros vinculados a glosas y generación de informes ejecutivos de posturas.
       - **Transiciones históricas:** Integración de los ciclos 2022 → 2023 (Boric vs Piñera) y 2018 → 2019 (Piñera vs Bachelet).
     - **Q1 2027 (Planificado):**
       - Cruce de órdenes de compra reales de ChileCompra contra glosas aprobadas.
       - API cívica abierta y descargas para periodismo de datos.

---

## 2. Archivos a Modificar
1. `src/interfaz.html`:
   - Inyectar el botón en el header (junto al selector de transiciones).
   - Inyectar el modal de Novedades & Roadmap accesible con cierre vía botón `✕` y tecla `Esc`.
   - Renderizado dinámico seguro de tabs (*Novedades* / *Hoja de Ruta*) usando `document.createElement` / `textContent` (0 uso de `innerHTML`).
2. Recompilación y sincronización:
   - Ejecutar `uv run python compilar_dist.py`.
   - Asegurar sincronización exacta de `dist/` a `docs/`.

---

## 3. Protocolo de Verificación Obligatorio
1. `uv run pytest tests/` (deben pasar los 120 tests existentes + tests para el modal si aplica).
2. Pruebas de estrés Node.js si corresponde.
3. Gates del arnés MyWorld:
   - `powershell -ExecutionPolicy Bypass -File .myworld-harness/harness.ps1 preflight`
   - `powershell -ExecutionPolicy Bypass -File .myworld-harness/harness.ps1 run-gate quality`
   - `powershell -ExecutionPolicy Bypass -File .myworld-harness/harness.ps1 run-gate security`
4. Commit atómico local de la feature.

---

## 4. Prompt para el Nuevo Chat
```text
Hola Antigravity. Por favor lee el archivo de handoff en:
c:\Users\evega\OneDrive\Documents\Obsidian\MyWorld\2 - Project\P149 - De la Glosa a la Calle\deploy\inbox\2026-10-06_handoff_novedades_roadmap.md

Implementa el botón y modal de Novedades y Roadmap (incluyendo el hito de YouTube para Q4) en deploy/src/interfaz.html, compila a dist/ y docs/, corre los tests y pasa los gates del arnés.
```
