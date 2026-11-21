# Impacto 2026-11-21 (b) — Publicación en GitHub y Fase 2 (replay)

↑ [Índice de impacto](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-21 |
| **Sesión** | [`../sesiones/2026-11-21-b-publicacion-y-fase-2.md`](../sesiones/2026-11-21-b-publicacion-y-fase-2.md) |
| **Rama / commits** | `main` · commit de la Fase 2 |
| **Estado** | Verificado |

## 1. Qué se va a tocar

| Zona | Archivo / contrato | Otros consumidores |
|---|---|---|
| SDK | `Recorder`, `RecordedRun.call_tool` (archivo `sdk/recorder.py`) | Demo, CLI, todo flujo instrumentado |
| Aplicación | `RecordingService.start` (nuevo kwarg `replay_of`) | SDK; tests de aplicación |
| Composición | `build_application` cablea `ReplayService` | CLI, tests |
| Demo | `run_toy_agent` (nuevo kwarg `replay_of`) | CLI, tests de aceptación |
| Formato | `run.started` puede llevar `replay_of` en el payload | Inspector; el esquema v0.1.0 no cambia (payload libre) |

## 2. Qué funciona hoy y qué le podría pasar

| Id | Comportamiento | Qué le podría pasar | Riesgo | Mitigación |
|---|---|---|---|---|
| CP-003…005 | Redacción antes de persistir | El camino de replay escribe eventos sin pasar por el pipeline | **Alto** | El replay usa el mismo `session.capture`; grep de la API key en disco tras replay: 0 |
| CP-008 | Fallo ⇒ run no completo | Un replay divergente queda `completed` | **Alto** | El context manager marca `failed`; test lo comprueba |
| CP-001/002 | Secuencia del agregado | — | Bajo | Sin cambios en `Run` |
| CP-019 | Contrato de la CLI | Comando nuevo rompe los existentes | Bajo | Tests de CLI previos en verde |
| (nuevo) | Grabar sigue ejecutando herramientas | Refactor del context manager rompe el modo grabación | Medio | Toda la suite previa (128) en verde |

## 3. Lo que se descubrió al analizar

- En replay no hay ningún caso legítimo de `ALLOW`: la política de efectos se mueve a la Fase 3 → [ADR-010](../forked/decisiones-arquitectura/ADR-010-replay-estricto-sin-politica.md).
- Cambiar el monto del demo no diverge en la llamada 1 ni la 2, sino en la **3** (`send_email`, cuyo cuerpo cambia): el
  test fija ese número para documentar que la divergencia se detecta donde de verdad ocurre.

## 4. Verificación posterior

| Id | Cómo se verificó | Resultado |
|---|---|---|
| Todos | `uv run pytest` | OK — 138 passed |
| CP-022 | Mutación: replay ejecuta `fn` | OK — 7 rojos |
| CP-023 | Mutación: no comparar nombre/clase | OK — 1 rojo |
| CP-025 | Mutación: no exigir consumo total | OK — 1 rojo |
| CP-003 | Smoke real: `record` + `replay` + grep `sk-toy` en el store | OK — 0 coincidencias; outbox con 1 mensaje |
| Estáticos | ruff check · ruff format --check · mypy strict | OK |

## 5. Comportamientos nuevos que pasan a protegidos

CP-022 a CP-025 en [`comportamientos-protegidos.md`](comportamientos-protegidos.md#replay).
