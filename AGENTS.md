# P149 — contrato del repositorio de software

El repo independiente es deploy/. Preservar la arquitectura FastAPI/SQLite/DuckDB. No desplegar ni publicar sin autorización específica. Las fuentes en ../src se mantienen iguales a la copia de deploy para los módulos compartidos. Los gates se ejecutan sobre este repositorio.

<!-- myworld-harness:start version=1.0.0 sha256=a4e53200433a0e3a39449e1c244fc071c20ad7bb30770b0af20f3f19cc7b1e65 -->
## Harness MyWorld v1

<!-- Este contenido está administrado por MyWorld. Las reglas locales adicionales se conservan. -->

- Antes de escribir, lee `MYWORLD-HARNESS.json` y ejecuta `.myworld-harness/harness.ps1 preflight`.
- El preflight inspecciona locks locales y el vault configurado. Declarar `MYWORLD_VAULT`, `MYWORLD_OWNER`, `MYWORLD_HOST` y `MYWORLD_SESSION` en el proceso cuando se use custodia central; identidad propia exige coincidencia exacta y lease vigente. Un lock ajeno vencido se recupera explícitamente.
- Un resultado `pending` no acredita aprobación completa. Ejecutar solo controles aplicables y registrar evidencia; no transformar ausencia de pruebas en `not_applicable` sin razón.
- El bundle incluye gates y validadores; coordinación y bandejas interproyectos usan el CLI canónico del vault. Auditar deriva con `rules audit --repositories --json` desde la fuente.
- Toda tarea no trivial debe tener un `task_id` estable. En repositorios GitHub, el Issue es el ticket canónico y debe conservar ese `task_id`.
- Un agente trabaja en una tarea, rama o worktree y superficie de escritura declarada; el lock representa custodia temporal, no propiedad permanente.
- No mezcles, reviertas ni elimines cambios ajenos.
- Si cambia el agente responsable, genera un handoff estructurado con el mismo `task_id`, revisión exacta, cambios, archivos, pruebas, riesgos, pendientes, rollback e `integration_owner`; libera el lock y el receptor adquiere uno nuevo tras verificar la revisión.
- Ejecuta los gates aplicables y entrega evidencia verificable; no declares pruebas no ejecutadas.
- Tests/verify comprueban comportamiento; RDD autoriza el candidato exacto revisado antes de commit/push/PR/deploy cuando corresponda.
- Un release requiere recibo previo validado. El corte local conserva las pruebas registradas; `--publish` y `--semantic-authorized` solo se usan con autorización específica para publicación o procesamiento externo.
- No imprimas ni almacenes secretos, tokens, cookies o datos personales innecesarios.
- Enviar, publicar, desplegar, borrar, pagar o modificar credenciales/permisos requiere autorización vigente, explícita y específica.
- Todo impedimento se registra como pendiente estructurado y no detiene trabajo independiente.
- Antes de integrar, entrega `task_id`, base revision, cambios, archivos, pruebas, riesgos, pendientes y rollback.
<!-- myworld-harness:end -->
