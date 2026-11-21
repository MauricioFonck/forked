# `contexto/PLANTILLAS/` — Plantillas de documentación

↑ [Memoria central](../README.md)

> **Navegación:** [← Memoria de FORKED](../README.md) · [Contextos](../modulos/README.md) · [Convenciones](../forked/convenciones.md)

Plantillas estandarizadas para que la memoria sea consistente, exhaustiva y legible tanto para personas como para IA.
Las plantillas de bitácora, impacto, fallo y revisión viven junto a su carpeta.

## Catálogo

| Plantilla | Ámbito | Destino al usarla | Descripción |
|---|---|---|---|
| [`plantilla-modulo.md`](plantilla-modulo.md) | Contexto acotado | `contexto/modulos/<contexto>/README.md` | Responsabilidad, archivos por capa, puertos, reglas, tests |
| [`plantilla-archivo.md`](plantilla-archivo.md) | Archivo Python | `contexto/modulos/<contexto>/<archivo>.md` | Ficha técnica de un módulo `.py` (pasada profunda) |
| [`plantilla-adr.md`](plantilla-adr.md) | Decisión | `contexto/forked/decisiones-arquitectura/ADR-NNN-<tema>.md` | Contexto, decisión, alternativas, consecuencias |
| [`../sesiones/PLANTILLA.md`](../sesiones/PLANTILLA.md) | Bitácora | `contexto/sesiones/AAAA-MM-DD-<tema>.md` | Qué se hizo en una sesión de IA |
| [`../impacto/PLANTILLA.md`](../impacto/PLANTILLA.md) | Impacto | `contexto/impacto/AAAA-MM-DD-<tema>.md` | Qué podría romperse antes de editar |
| [`../errores/PLANTILLA.md`](../errores/PLANTILLA.md) | Fallo | `contexto/errores/{bugs,errores}/…` | Síntoma, causa raíz y concepto que faltó |
| [`../revisiones/PLANTILLA.md`](../revisiones/PLANTILLA.md) | Revisión | `contexto/revisiones/AAAA-MM-DD-<tema>.md` | Hallazgos marcables de una revisión |

## Cómo utilizarlas

1. Copia la plantilla al destino de la tabla y borra las líneas de ayuda.
2. Completa cada sección con información verídica sacada del código (con ruta y, si aplica, línea).
3. Enlaza el documento nuevo desde el índice de su carpeta: el guardián del grafo falla si queda huérfano.
