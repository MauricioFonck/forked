# Revisión 2026-11-21 — Preparación del repositorio

↑ [Revisiones](README.md)

| | |
|---|---|
| **Alcance** | `README.md`, `CLAUDE.md` y los 16 documentos de `docs/` (propuesta técnica v0.2) |
| **Contra** | El primer prompt de [`docs/13`](../../docs/13-claude-code-execution-plan.md) (9 puntos) |
| **Revisor** | Claude Code (Opus 5.5), sesión [2026-11-21](../sesiones/2026-11-21-arranque-fase-0-y-1.md) |

## 1. Problema y alcance exacto de v0

Grabar localmente un flujo de juguete instrumentado, reproducir sus observaciones sin repetir escrituras, bifurcar en un
checkpoint con **una** intervención (reemplazar un resultado de herramienta), comparar con invariantes
`verified/violated/unknown` y exportar un paquete de evidencia verificable offline. Sin nube, sin UI, sin prueba causal.

## 2. Contradicciones, decisiones faltantes, supuestos riesgosos y afirmaciones sin sustento

- [x] **[Medio]** `CLAUDE.md` «Read first» numera dos veces el 3. → corregido; además agrega `contexto/` al inicio.
- [x] **[Grave]** Tres vocabularios de efectos/afirmaciones/mayúsculas no coinciden (FR-009 vs CIP §6.5; `CLAUDE.md`
  vs CIP §6.7; `VERIFIED` vs `"verified"`). → [ADR-003](../forked/decisiones-arquitectura/ADR-003-vocabulario-cip.md).
- [x] **[Medio]** El ejemplo del CIP pone `"status": "verified"` dentro de la **declaración** del invariante: mezcla
  declaración y resultado. → ADR-003 los separa.
- [ ] **[Grave]** `docs/05` §5.8 permite que `EvaluateEffect` devuelva `SIMULATE`, pero `CLAUDE.md` prohíbe «simular en
  silencio y reportarlo como real». → condición en la [spec 003](../docs/superpowers/specs/003-replay-de-observaciones/spec.md):
  `SIMULATE` solo explícito, marcado en evidencia y nunca contado como resultado real.
- [x] **[Medio]** El MVP lista SQLite; la Fase 1 dice «si hace falta». → [ADR-004](../forked/decisiones-arquitectura/ADR-004-persistencia-fase-1.md): diferido.
- [x] **[Medio]** Nombre `forked` ocupado en PyPI. → [ADR-002](../forked/decisiones-arquitectura/ADR-002-nombre-distribucion.md).
- [x] **[Medio]** Faltaba decidir base de secuencia, formato de ids y reloj. → [ADR-009](../forked/decisiones-arquitectura/ADR-009-secuencia-ids-tiempo.md).
- [x] **[Medio]** Faltaba qué hacer con payloads sobre el límite y con falsos positivos de redacción. → [ADR-007](../forked/decisiones-arquitectura/ADR-007-omitir-no-truncar.md).
- [x] **[Grave]** No se menciona que los **mensajes de excepción** pueden contener secretos. → redactados (CP-005).
- [ ] **[Medio]** «Capture completeness» necesita puntos de captura declarados, pero ningún documento dice quién los
  declara. → resuelto para la Fase 1 con `AdapterCapabilities.capture_points`; falta para adaptadores de framework.
- [ ] **[Medio]** Ningún documento define qué es un checkpoint portable (abierta §12.2.2). Bloquea la Fase 3.
- [ ] **[Menor]** Políticas OSS planificadas para la Fase 6, pero el repositorio será público antes. → adelantadas
  (`SECURITY.md`, `CONTRIBUTING.md`, plantillas). **Falta activar** el reporte privado de vulnerabilidades en GitHub.
- [ ] **[Menor]** Afirmación a vigilar: el README original no exagera; mantener «borrador/propuesta/hipótesis» hasta
  pasar la [puerta de arte previo](../investigacion/arte-previo.md).

## 3. Estructura mínima de paquetes y dirección de dependencias

Implementada: ver [arquitectura](../forked/arquitectura.md) y [diagrama hexagonal](../diagramas/hexagonal.md).
`domain` → solo stdlib; `application` → `domain` + puertos; `adapters` implementan puertos; `bootstrap` cablea.

## 4. Modelos tipados de dominio

`Run` (+ `RunStatus`, `RunSnapshot`), `Event` (+ `EventType`, `CaptureStatus`, `EventDraft`), `EffectClass`,
`AdapterCapabilities`, `EnvironmentFingerprint`. Detalle en el [contexto `runs`](../modulos/runs/README.md).

## 5. Esquema JSON y 5 fixtures representativos

[Sobre de evento](../protocolo/sobre-de-evento.md); fixtures en `tests/fixtures/events/v0.1/` (inicio, llamada
redactada, resultado con traza, resultado omitido, fallo).

## 6. Tests de orden, esquema, redacción, eventos malformados y metadatos faltantes

Implementados (123). Mapa a comportamientos en [comportamientos protegidos](../impacto/comportamientos-protegidos.md).

## 7. Plan con tareas pequeñas y criterios de aceptación

[Spec 001](../docs/superpowers/specs/001-cimientos-del-repositorio/spec.md) y
[spec 002](../docs/superpowers/specs/002-grabador-local/spec.md) con sus `plan.md` y `tasks.md`.

## 8. Puertos genuinos vs. abstracciones prematuras

| Genuino (hay adaptador real o test que lo exige) | Prematuro (no se creó) |
|---|---|
| `EventLog`, `RunRepository` (disco vs. memoria) | `BaseRepository[T]` genérico |
| `Clock`, `IdGenerator` (tests deterministas) | Unit of Work (no hay transacciones multi-recurso) |
| `EnvironmentProbe` (plataforma vs. fijo en tests) | `AdapterRegistry` (un solo adaptador) |
| — | `ArtifactStore` (llega con la Fase 4), `EffectPolicyEvaluator` (Fase 2) |

## 9. Chequeo automático de límites y estrategia de contratos

[ADR-005](../forked/decisiones-arquitectura/ADR-005-guardianes-pytest.md): guardián AST de dependencias + suite de
contrato que corre igual sobre el adaptador real y el doble en memoria.
