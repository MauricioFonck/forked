# Impacto 2026-11-21 (d) — Fase 4: paquete de evidencia y verificador offline

↑ [Índice de impacto](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-21 |
| **Sesión** | [`../sesiones/2026-11-21-d-fase-4-evidencia.md`](../sesiones/2026-11-21-d-fase-4-evidencia.md) |
| **Rama / commits** | `main` · commit de la Fase 4 |
| **Estado** | Verificado |

## 1. Qué se va a tocar

| Zona | Archivo / contrato | Otros consumidores |
|---|---|---|
| Comparación | serialización movida de la CLI a `Comparison.as_dict()` | `forked compare --json`, exportador |
| Store | nuevo método `raw_files` (solo lectura) | Exportador |
| Composición | `Application.export`, `export_evidence`, `verify_package`; `InspectRun`/`CompareRuns` compartidos | CLI, tests |
| CLI | comandos nuevos `export`, `verify` | Usuarios, CI |

## 2. Qué funciona hoy y qué le podría pasar

| Id | Comportamiento | Qué le podría pasar | Riesgo | Mitigación |
|---|---|---|---|---|
| CP-019 | `compare --json` | Cambia la salida al mover la serialización | Medio | Mismo diccionario; test de CLI de comparación en verde |
| CP-003…005 | Sin secretos en disco | El paquete copia artefactos con un secreto que escapó a la redacción | **Alto** | Escaneo de credenciales al exportar (CP-039) |
| CP-012/014 | Store falla cerrado | Abrir el paquete como store acepta datos alterados | **Alto** | La validez solo se evalúa si la integridad pasa; el store sigue validando línea a línea |
| CP-026 | Padre intacto | El exportador escribe en el store | Medio | Solo `read_bytes`; destino debe estar vacío |

## 3. Lo que se descubrió al analizar

- Un manifiesto sin firma no puede probar autoría: se declaró como limitación dentro del propio paquete y se añadió
  la validez por recálculo, que atrapa la reescritura con hashes corregidos cuando altera lo que la evidencia sostiene.
- `rglob` no sigue symlinks a directorios por defecto, pero un symlink a archivo sí se leería: se rechaza explícitamente.

## 4. Verificación posterior

| Id | Cómo se verificó | Resultado |
|---|---|---|
| Todos | `uv run pytest` | OK — 178 passed, 1 skipped (symlink en Windows) |
| CP-035 | Mutaciones: no comparar hash / ignorar extras | OK — 2 / 1 rojos |
| CP-036 | Mutaciones: no revisar afirmaciones / `ok` ignora validez | OK — 2 / 2 rojos |
| CP-037 | Mutación: no revisar formato | OK — 1 rojo |
| CP-038 | Mutaciones: toda ruta es segura / sobrescribir | OK — 7 / 1 rojos |
| CP-039 | Mutación: sin escaneo de credenciales | OK — 1 rojo |
| CP-034 | Smoke real: export, borrar `runs/`, verify | OK |
| Estáticos | ruff · format · mypy strict | OK |

## 5. Comportamientos nuevos que pasan a protegidos

CP-033 a CP-039 en [`comportamientos-protegidos.md`](comportamientos-protegidos.md).
