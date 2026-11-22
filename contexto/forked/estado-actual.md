# Estado actual

↑ [Memoria central](../README.md)

> Documento **vivo**: se actualiza cada vez que una fase avanza. Última revisión: **2026-11-21**
> ([sesión de arte previo, LangGraph y release](../sesiones/2026-11-22-g-arte-previo-langgraph-y-release.md)).

## Resumen

| Fase | Alcance | Estado | Spec |
|---|---|---|---|
| 0 | Cimientos del repositorio, CI, políticas OSS, guardianes | ✅ Hecha | [001](../docs/superpowers/specs/001-cimientos-del-repositorio/spec.md) |
| 1 | Grabador local + inspector + CLI `record`/`inspect`/`runs` | ✅ Hecha | [002](../docs/superpowers/specs/002-grabador-local/spec.md) |
| 2 | Replay de observaciones grabadas, fallo cerrado | ✅ Hecha | [003](../docs/superpowers/specs/003-replay-de-observaciones/spec.md) |
| 3 | Ramas, una intervención, política default-deny, invariantes, comparación | ✅ Hecha | [004](../docs/superpowers/specs/004-ramas-e-intervencion/spec.md) |
| 4 | Paquete de evidencia + verificador offline | ✅ Hecha | [005](../docs/superpowers/specs/005-paquete-de-evidencia/spec.md) |
| 5 | Puente OpenTelemetry, primer adaptador de framework (Pydantic AI), FCRB | ✅ Hecha (sin reproducción independiente) | [006](../docs/superpowers/specs/006-adaptador-y-benchmark/spec.md) |
| 6 | Alfa pública y comunidad | ✅ Hecha: pre-release `v0.1.0a1` en GitHub (sin PyPI) | [007](../docs/superpowers/specs/007-alfa-publica-y-documentacion/spec.md) |

## Qué funciona hoy (verificado)

- `forked record toy-agent` graba un agente de juguete con 3 herramientas (`pure_local`, `external_read`,
  `external_write`), redacta su API key falsa y reporta 100 % de completitud, 0 evidencia faltante.
- `forked inspect <run> [--events] [--json] [--strict]` reporta estado efectivo, validez de secuencia, completitud contra
  puntos declarados, eventos redactados/omitidos y la lista de evidencia faltante.
- Un run interrumpido (metadatos en `recording`, cola del log perdida) se reporta como `incomplete` con cada punto de
  captura no observado.
- Esquema de evento v0.1.0 publicado en [`spec/cip/v0.1/`](../../spec/cip/v0.1/event.schema.json) con 5 fixtures dorados.
- `forked replay <run>` re-ejecuta el flujo contestando cada herramienta con lo grabado: **0 herramientas
  ejecutadas**, outbox intacto, mismo resultado; cualquier divergencia u observación faltante falla cerrado
  ([contexto `replay`](../modulos/replay/README.md)).
- `forked branch <run> --at 3 --value 0.5` bifurca en un `tool.call`, reemplaza su resultado y re-ejecuta: antes
  del checkpoint replay, después replay si no cambió o política default-deny (el email nuevo se **deniega**).
  `forked compare` da diferencias por paso y de resultado, 5 invariantes y el nivel de afirmación
  ([contexto `branches`](../modulos/branches/README.md)).
- `forked export <base> <rama> --out DIR` y `forked verify DIR`: paquete determinista con SHA-256 por artefacto;
  el verificador funciona solo con el paquete y separa integridad de validez, recalculando la comparación
  ([contexto `evidence`](../modulos/evidence/README.md)).
- Un agente real de **Pydantic AI** (modelo guionado, sin red) se graba, reproduce, bifurca, compara y exporta con
  `uv run python -m examples.pydantic_ai_expense_agent` ([contexto `integrations`](../modulos/integrations/README.md)).
- `forked otel-export` / `otel-import`: puente OTLP/JSON ([formato](../protocolo/puente-opentelemetry.md)).
- `python -m benchmarks.fcrb`: 10 escenarios + línea base de logs simples ejecutada; 10/10 `pass`; costo de captura
  ≈ 2,4 ms por llamada ([contexto `benchmarks`](../modulos/benchmarks/README.md)). **Provisional: no validado.**
- Documentación de usuario en `docs/guide/` (6 páginas), ejemplo mínimo sin framework, notas de versión **borrador**,
  plantilla de reporte de reproducción y guardián de documentación ([ADR-014](decisiones-arquitectura/ADR-014-documentacion-publica-y-puerta-de-release.md)).
- La rueda (73 KB) se instala y ejecuta fuera del repo; el sdist pesa 116 KB.
- Segundo adaptador: **LangGraph** (`forked_tool_node`); el benchmark mide su viaje en el tiempo como línea base (S04: repitió
  el email, FORKED 0) y S10 compara tres adaptadores ([ADR-016](decisiones-arquitectura/ADR-016-adaptador-langgraph-y-linea-base.md)).
- **Primera pasada de arte previo** publicada ([`docs/15`](../../docs/15-prior-art-matrix.md), [ADR-015](decisiones-arquitectura/ADR-015-posicionamiento-tras-el-arte-previo.md)):
  lo básico ya existe; la diferencia se afirma solo como combinación acotada. **Puerta parcialmente abierta.**
- **`forked report`**: un HTML autocontenido (sin JavaScript, CSP estricta, determinista) con línea de tiempo, diagrama del fork,
  invariantes y evidencia verificada ([ADR-017](decisiones-arquitectura/ADR-017-reporte-html-autocontenido.md)).
- **293 tests** (1 se salta en Windows: symlinks) (unidad, contrato, seguridad, integración, aceptación, guardianes) + ruff + mypy strict en verde, y
  60 mutaciones dirigidas detectadas (una sobrevivió y generó un test nuevo, ver la
  [bitácora de la Fase 3](../sesiones/2026-11-21-c-fase-3-ramas.md#6-cómo-verificar)). Comandos en las bitácoras
  ([Fases 0–1](../sesiones/2026-11-21-arranque-fase-0-y-1.md#6-cómo-verificar),
  [Fase 2](../sesiones/2026-11-21-b-publicacion-y-fase-2.md#6-cómo-verificar)).
- Repositorio público en GitHub (`MauricioFonck/forked`), CI en verde en Linux 3.11–3.14, Windows y macOS.

## Qué NO funciona todavía

- El manifiesto no está firmado: la integridad es consistencia interna ([ADR-012](decisiones-arquitectura/ADR-012-paquete-de-evidencia.md)).
- Dos frameworks (Pydantic AI, LangGraph); solo se graban herramientas. El benchmark **no tiene reproducción
  independiente** y solo dos líneas base ejecutadas.
- La puerta de arte previo sigue **parcialmente abierta** ([arte previo](../investigacion/arte-previo.md)).
- Una sola intervención (`replace_recorded_observation`) y una sola política (`default-deny/1`), sin
  aprobaciones del usuario.
- No hay índice SQLite: listar runs recorre el directorio ([ADR-004](decisiones-arquitectura/ADR-004-persistencia-fase-1.md)).

## Próximo paso

El release `v0.1.0a1` está **publicado como pre-release en GitHub** y Discussions está habilitado; **PyPI no** (requiere
el token del dueño). Ver la [bitácora](../sesiones/2026-11-22-g-arte-previo-langgraph-y-release.md#5-qué-quedó-pendiente--decisiones-para-el-usuario).
Después, por valor: la **matriz de arte previo** (puerta abierta), una **reproducción independiente** del benchmark y
un segundo adaptador (LangGraph) con su línea base de viaje en el tiempo nativo.
