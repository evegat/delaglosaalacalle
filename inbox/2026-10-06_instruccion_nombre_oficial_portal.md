---
tipo: recurso
subtipo: instruccion
proyecto: P149
estado: procesado
fecha: 2026-10-06
autor: "[[Eduardo Vega Toledo]]"
relacionados:
  - "[[00 - Home.md]]"
  - "[[01 - Bitacora.md]]"
---

# Instrucción de Naming Oficial: Portal "De la Glosa a la Calle"

**Fecha de instrucción:** 2026-10-06 22:39 CLT  
**Autor:** [[Eduardo Vega Toledo]]  
**Estado:** Procesado y sincronizado en código, build y notas del proyecto  

---

## 1. Instrucción Directa de Eduardo

> "el nombre deberia ser:  
> **Portal "De la Glosa a la Calle", observatorio de prioridades fiscales y su impacto en los habitantes de Chile**"

---

## 2. Aplicación y Alcance Técnico

La denominación canónica e institucional del producto reemplaza cualquier título provisorio previo y queda fijada transversalmente en todos los puntos de contacto:

1. **Código Fuente Frontend (`deploy/src/interfaz.html`):**
   - Tag `<title>`: `Portal "De la Glosa a la Calle" — Observatorio de prioridades fiscales y su impacto en los habitantes de Chile`
   - Cabecera (`<header>`):
     - Marca: `PORTAL "DE LA GLOSA A LA CALLE"`
     - Submarca: `Observatorio de prioridades fiscales y su impacto en los habitantes de Chile`
   - Hero Section (`<section class="hero-limpio">`):
     - `<h1>`: `Portal "De la Glosa a la Calle"`
     - `<h2>`: `Observatorio de prioridades fiscales y su impacto en los habitantes de Chile`
   - Pie de Página (`<footer>`):
     - `Portal "De la Glosa a la Calle" · Lectura cívica del presupuesto...`
   - Changelog v1.2.0 (`NOVEDADES_DATA`):
     - `titulo`: `'Observatorio de prioridades fiscales y su impacto en los habitantes de Chile'`

2. **Compilados de Distribución y Hosting:**
   - Sincronizado a `deploy/dist/index.html` y `deploy/dist/assets/relato.js`
   - Sincronizado a `deploy/docs/index.html` y `deploy/docs/assets/relato.js` (GitHub Pages)

3. **Gobernanza y Ficha del Proyecto en MyWorld:**
   - [[00 - Home.md]]: H1 formal actualizado y entrada canónica en la *Ficha Ejecutiva para Reuniones (Lectura en 2 minutos)*.
   - [[01 - Bitacora.md]]: H1 formal alineado y registro del hito de identidad y naming.

4. **Verificación Automatizada:**
   - Validado en la suite de pruebas unitarias (`tests/test_interfaz_scrollytelling.py`) garantizando la presencia exacta del nombre en fuentes y compilados, con 121/121 tests PASS, 0 sinks inseguros (`innerHTML` erradicado) y gates de arnés aprobados.
