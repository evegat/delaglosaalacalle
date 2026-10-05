# P149 — Resultado local del bloque intensivo

El software solicitado para T04–T09 está implementado y verificado en `deploy/`.
El bloque completo sigue **parcial**: el lector del Vault y el commit documental
P063 requieren resolver el arnés raíz ausente. No hubo publicación, despliegue,
push, envío ni procesamiento documental externo.

## Alcance y fuentes

- Tarea: `FEAT-P149-MEJORA-CIVICA-20261004`; rama `EduCodex/p149-mejora-civica-20261004`.
- Base: `4ba731d6e90adec487134a37e051ca3490df17ac`.
- Instrucciones: contrato MyWorld, `deploy/AGENTS.md`, `MYWORLD-HARNESS.json` y
  `../odd/tasks/mejora-civica-20261004.md`. Espejo operacional Engram registrado.
- Se retomaron cambios previos del backend y del arnés, conservados y verificados.
  Las fuentes originales de `../src/` no se sincronizaron ni sobrescribieron por
  la restricción vigente de trabajar en `deploy/`. No se acredita paridad con ellas.

## Resultado por tarea

| Tarea | Resultado comprobado | Límite |
|---|---|---|
| T04 | Cruce por Partida/Capítulo/Programa/Subtítulo/Ítem/Asignación; nombres separados de identidad; NULL, cero explícito, discordancias y unidades diferenciadas; cálculo decimal | Variación real sin IPC oficial verificado del período queda NULL; no hay tasa predeterminada |
| T05 | XLSX, CSV y PDF estructurado; SHA256, SQLite transaccional, idempotencia incluso concurrente, rechazos NDJSON, exportación DuckDB nueva | PDF requiere seis códigos explícitos o tres en encabezado + tres en fila, años y unidad/moneda explícitos; ambiguos/OCR se rechazan |
| T06 | n, P25/P50/P75, desviación muestral, unidad, moneda, territorio, período, fuentes y deduplicación; equivalencia con rango | Catálogo operativo sin observaciones verificadas cargadas; ninguna cifra ficticia ni media nacional |
| T07–T08 | Scrollytelling de cuatro pasos con SVG fijo que cambia al avanzar; buscador con/sin tildes; filtro por servicio; teclado, lectura sin JS, CSS de movimiento reducido; registro de preguntas conservado | No constituye certificación integral WCAG ni prueba de comprensión con personas |
| T09 | Suite completa, compilación local, quality/security y continuidad; commits locales trazables | No acredita funcionamiento en producción, restauración ni fuentes institucionales completas |

## Pruebas y evidencia

- **68 pruebas PASS**, una advertencia de deprecación Starlette/httpx;
  [log completo](pytest-20261004.log).
- Distribución: backend 11; comparación 26; ingesta 15; equivalencias 12; interfaz 4.
- RED observado antes de cada módulo; regresiones adicionales reprodujeron
  interpretación decimal XLSX errónea, n inflado por copias, páginas PDF ambiguas
  ignoradas y unidades presupuestarias ausentes. GREEN tras las correcciones.
- Quality y security **PASS**, sin excepciones. Preflight: perfil, adaptador,
  custodia exacta, repositorio y hooks PASS; árbol con cambios previos fue pending
  no bloqueante y se conservó. La continuidad global terminó PASS, 14 controles.
- Se reparó la compilación local que apuntaba a un script ausente. El contenedor
  pasó a usuario sin privilegios y conserva escritura SQLite sobre `/app/data`;
  no se construyó ni desplegó la imagen productiva.
- Git tenía seis `desktop.ini` dentro de `refs/`: se conservaron en
  `.git/myworld-metadata-backups/` para permitir el escaneo real del historial.
  No se borraron. Se preservó también una rama de respaldo de los commits propios
  antes de separarlos por tarea.
- Navegador: 320/390/1280 px sin desborde; escena SVG sincronizada tras corregir
  el observer; `educacion` y `educación` dan los mismos 34 resultados; JUNAEB filtra
  11; Tab pasa del buscador al selector Servicio. Sin errores de consola observados.
- Contraste calculado: texto/papel 15,37:1; verde/papel 13,24:1; texto/fondo suave
  14,38:1. Se revisó CSS de movimiento reducido, sin certificar lectores de pantalla.
- HTML + CSS + JS: **7.334 bytes gzip**, bajo 50 KiB. El HTML compilado usa assets
  locales compatibles con CSP; sin trackers, tipografías remotas ni bibliotecas UI.
- [Evidencia estructurada, SHA256 y lista de archivos](qa-20261004.json).

## Uso local de la ingesta

Desde `deploy/`, con fuentes públicas revisadas y sin cambiar originales:

```powershell
uv run --with pypdf python src/ingesta_batch.py "RUTA/FUENTE.xlsx" "RUTA/FUENTE.pdf" --sqlite data/ingesta-local.sqlite3 --rechazados inbox/rechazados.ndjson --duckdb-nuevo data/ingesta-revision-AAAAMMDD.duckdb
```

Columnas Excel/CSV: `Partida`, `Capítulo`, `Programa`, `Subtítulo`, `Ítem`,
`Asignación`, `Denominación`, años `2025`/`2026`, `Unidad`, `Moneda`.
No se inventan códigos para subtotales, celdas vacías o fórmulas no verificadas.
El exportador DuckDB exige destino nuevo y no reemplaza la base usada por FastAPI.
Para leer el resultado local en la API, configurar `P149_INGESTA_DB` con esa SQLite.
La trazabilidad acredita extracción y procedencia del archivo, no autenticidad
institucional: confirmar la fuente y la cobertura antes de hacer afirmaciones.

El catálogo `data/costos_referencia.csv` exige `servicio,monto,cantidad,unidad,
moneda,territorio,periodo,fuente,verificada`; solo `verificada=true` documentada
habilita observaciones. Un costo estimado sin cantidad queda excluido. `IndiceIPC`
requiere índices comparables, fuente INE, períodos y verificación explícita.

## Otros frentes y pendientes

- P063: paquete documental validado, 127/127 hashes originales conservados,
  41 enlaces relativos resueltos, 72 movimientos finales y 18 versiones previas.
  Ocho editables/referencias convertidos localmente con MarkItDown y revisados.
  Bitácora y checkpoint registrados. Curso sigue en movimiento; no se distribuyó.
- `audit_commitments.py` todavía falla por el respaldo P061. No se escribió código
  del lector ante el preflight raíz FAIL. El pendiente
  `PND-MYWORLD-VAULT-CONFIABLE-LECTORES-20261004` sigue blocking, con evidencia vigente.
- El commit P063 no se realizó: quality/security raíz FAIL por infraestructura
  ausente. La decisión de contrato acotado sin hooks globales se consultó y continúa
  pendiente; no se dio por aprobada por silencio.
- Antes de uso operativo: probar originales DIPRES representativos, cargar costos
  verificados e IPC apropiado, revisar con Eduardo y usuarios, y validar recuperación.
  Nada de esto queda reemplazado por las pruebas sintéticas.

Siguiente acción: revisar el scrollytelling local y resolver el contrato acotado
para terminar el Frente 1. La disponibilidad de cómputo no se convirtió en trabajo
artificial ni en una afirmación de cinco horas ejecutadas.
