# Convenciones

↑ [Memoria central](../README.md)

## 1. Código

- **Python ≥ 3.11**, `from __future__` no hace falta. Tipado completo; `mypy --strict` sobre `src` y `tests`.
- Imports **absolutos** (`from forked.domain…`); el guardián rechaza imports relativos.
- Dominio: `@dataclass(frozen=True, slots=True)` para objetos valor; `StrEnum` para vocabularios serializados (valores
  en minúscula, ver [ADR-003](decisiones-arquitectura/ADR-003-vocabulario-cip.md)). Nada de Pydantic.
- Errores: subclase de `ForkedError` con `code` estable. Nunca `raise Exception("…")`.
- Hora e ids **siempre** por puerto (`Clock`, `IdGenerator`) para que los tests sean deterministas.
- Un puerto existe solo si hay un adaptador real que aislar o un test que lo necesite. No crear carpetas vacías para
  imitar un diagrama.
- Textos libres que vengan de fuera (mensajes de excepción, salidas) pasan por el pipeline de redacción antes de
  persistirse.
- Estilo: `ruff check` + `ruff format`, línea de 100.

## 2. Tests

| Carpeta | Qué prueba | Regla |
|---|---|---|
| `tests/unit/domain/` | Invariantes y máquinas de estado | Sin disco, red ni frameworks |
| `tests/unit/application/` | Orquestación y caminos de fallo | Con dobles de `tests/fakes/` |
| `tests/contract/` | Contrato de cada puerto | **El doble y el adaptador real corren la misma suite** |
| `tests/security/` | Redacción en disco, traversal, artefactos malformados/manipulados | Un caso por amenaza de [`docs/07`](../../docs/07-security-and-privacy.md) |
| `tests/integration/` | CLI con `CliRunner` y disco temporal | Sin servicios externos |
| `tests/acceptance/` | Caso de uso completo, con la red bloqueada | Demuestra «offline» |
| `tests/guardians/` | Reglas estructurales (dependencias, esquema, grafo de `contexto/`) | Leen el código, no el comportamiento |

Toda funcionalidad lleva tests de **éxito, fallo, operación insegura y evidencia faltante**. Para reglas de seguridad,
se demuestra que el test muerde con una **mutación** (romper la regla a propósito, ver rojo, restaurar).

## 3. Git

- Rama principal `main`. Mensajes de commit en inglés, en imperativo (`Add recorder`, `Fix …`).
- Código + tests + documentación + bitácora + impacto van en el **mismo commit**.
- `.gitattributes` fuerza LF: fixtures y esquemas se comparan byte a byte.
- Nunca se commitea un store `.forked/` (aunque esté redactado puede contener datos sensibles).

## Mantenimiento de este contexto

| Si cambias… | Actualiza |
|---|---|
| **Cualquier cosa** (toda sesión que toque código) | Bitácora en [`sesiones/`](../sesiones/README.md) + análisis en [`impacto/`](../impacto/README.md) |
| Un contexto acotado (comportamiento, archivos, puertos) | Su README en [`modulos/<contexto>/`](../modulos/README.md) |
| Un contexto nuevo implementado | Su carpeta en `modulos/` + fila en [`modulos/README.md`](../modulos/README.md) y en §5 de la [memoria central](../README.md) |
| El sobre de evento o el formato en disco | [`protocolo/sobre-de-evento.md`](../protocolo/sobre-de-evento.md) + `spec/` regenerado + fixtures nuevos |
| La taxonomía o la política de efectos | [`protocolo/taxonomia-de-efectos.md`](../protocolo/taxonomia-de-efectos.md) + [diagrama](../diagramas/politica-efectos.md) |
| Una decisión arquitectónica | Nuevo ADR en [`decisiones-arquitectura/`](decisiones-arquitectura/README.md) + su fila en el índice y en §8 |
| Una fase que avanza | [`estado-actual.md`](estado-actual.md) + [`roadmap.md`](roadmap.md) + `CHANGELOG.md` |
| Evidencia sobre una hipótesis o escenario FCRB | [`investigacion/`](../investigacion/README.md) |
| **Arreglas un fallo no trivial** | Ficha en [`errores/`](../errores/README.md) + su índice |
| Un comportamiento que no puede romperse | Fila `CP-nnn` en [`comportamientos-protegidos.md`](../impacto/comportamientos-protegidos.md) con su test |
| Un trabajo de varias tareas | Carpeta en [`docs/superpowers/specs/`](../docs/superpowers/README.md) |
| Comandos, estructura o reglas para agentes | [`CLAUDE.md`](../../CLAUDE.md) y [`AGENTS.md`](../../AGENTS.md) |
| Algo visible para usuarios | `README.md` y `CHANGELOG.md` (inglés) |
