# Impacto 2026-11-21 — Arranque: Fase 0 (cimientos) y Fase 1 (grabador local)

↑ [Índice de impacto](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-21 |
| **Sesión** | [`../sesiones/2026-11-21-arranque-fase-0-y-1.md`](../sesiones/2026-11-21-arranque-fase-0-y-1.md) |
| **Rama / commits** | `main` · commit inicial del repositorio |
| **Estado** | Verificado |

## 1. Qué se va a tocar

Repositorio nuevo: no hay código previo que romper. El impacto relevante es **hacia adelante**: los contratos que nacen
hoy y que las Fases 2–4 van a consumir.

| Zona | Archivo / contrato | Otros consumidores (futuros) |
|---|---|---|
| Formato en disco | `events.jsonl` v0.1.0, `run.json` | Replay (Fase 2) lee `EventLog`; evidencia (Fase 4) hashea estos archivos |
| Esquema publicado | `spec/cip/v0.1/*.schema.json` | Terceros que validen artefactos; adaptadores de otros lenguajes |
| Puertos | `EventLog`, `RunRepository`, `Clock`, `IdGenerator`, `EnvironmentProbe` | Todo caso de uso nuevo |
| SDK | `Recorder.record()`, `RecordedRun.call_tool()` | Adaptadores de frameworks (Fase 5) |
| CLI | `record`, `inspect`, `runs`, códigos de salida | Scripts y CI de usuarios |

## 2. Qué funciona hoy y qué le podría pasar

| Id | Comportamiento | Qué le podría pasar | Riesgo | Mitigación |
|---|---|---|---|---|
| CP-003/004/005 | Secretos redactados antes de persistir | Un camino nuevo de texto libre (motivo de fallo, error de herramienta) que no pase por el pipeline | **Alto** | Todo payload y el motivo de fallo pasan por `CapturePipeline`; tests + mutaciones |
| CP-007/008 | Un parcial nunca parece completo | Que un error de disco o una caída deje el run como `completed` | **Alto** | `RECORDING` ⇒ `incomplete` al inspeccionar; `_abort` marca `incomplete`; comparar `next_sequence` con líneas |
| CP-012 | Artefactos malformados fallan cerrados | Saltar líneas malas «para ser tolerante» | **Alto** | Cada caso con test parametrizado y número de línea |
| CP-016 | Esquema estable | Cambiar el formato sin subir versión ni fixtures | Medio | Guardián de esquema + fixtures dorados |
| CP-015 | Regla de dependencias | Importar Pydantic en el dominio por comodidad | Medio | Guardián AST + mutaciones |
| CP-020 | Doble = adaptador | Un doble más permisivo que el disco | Medio | Suite de contrato parametrizada |

## 3. Lo que se descubrió al analizar

- `docs/` tiene tres vocabularios contradictorios (efectos, niveles de afirmación, mayúsculas) → [ADR-003](../forked/decisiones-arquitectura/ADR-003-vocabulario-cip.md).
- `forked` está ocupado en PyPI → [ADR-002](../forked/decisiones-arquitectura/ADR-002-nombre-distribucion.md).
- Un mensaje de excepción es un canal de fuga de secretos que la documentación no menciona → CP-005.
- La decisión `EvaluateEffect → SIMULATE` de `docs/05` §5.8 choca con «no simular en silencio» si no se marca en la
  evidencia → anotado en la [spec 003](../docs/superpowers/specs/003-replay-de-observaciones/spec.md).
- Todo hallazgo de la revisión: [revisión de preparación](../revisiones/2026-11-21-revision-de-preparacion.md).

## 4. Verificación posterior

| Id | Cómo se verificó | Resultado |
|---|---|---|
| Todos | `uv run pytest` | OK — 123 passed (+5 del guardián de grafo al cerrar la memoria) |
| CP-003/004/005, 007, 008, 012 | Mutación: desactivar la regla y correr la suite | OK — 14, 8, 1, 2, 1, 1 tests rojos respectivamente; árbol restaurado y suite en verde |
| CP-015 | Mutación: `import pydantic` en dominio, `import typer` en aplicación, adaptador de salida en la CLI | OK — el guardián falla en los tres casos |
| CP-017 | `test_toy_agent_end_to_end.py` con `socket.connect` bloqueado | OK |
| CP-021 | Mutación: huérfano, enlace roto, enlace con mayúsculas equivocadas | El tercero **no** mordía en Windows → arreglado ([E-001](../errores/errores/E-001-el-guardian-del-grafo-no-veia-mayusculas-en-windows.md)); ahora los tres en rojo |
| Estáticos | `uv run ruff check .` · `uv run ruff format --check .` · `uv run mypy` | OK — sin hallazgos |

## 5. Comportamientos nuevos que pasan a protegidos

CP-001 a CP-021, registrados en [`comportamientos-protegidos.md`](comportamientos-protegidos.md).
