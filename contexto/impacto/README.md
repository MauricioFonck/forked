# `impacto/` — Qué funciona hoy y qué le pasaría con cada cambio

↑ [Memoria central](../README.md)

> Antes de tocar una zona del sistema: **qué hace bien hoy** (y cómo se comprueba) y **qué le podría pasar** con la
> edición que se va a hacer. Después de tocarla: qué se verificó.

## El problema que resuelve

Un cambio tiene dos caras: lo que **añade** y lo que **puede quitar**. La segunda no se ve en el diff. En FORKED es más
grave que en un producto común: una regresión silenciosa no rompe una pantalla, **cambia lo que alguien concluye** de un
experimento (un secreto que vuelve a disco, un run parcial que se reporta completo, una escritura que se repite).

## Dos piezas

| Archivo | Qué es | Cuándo se toca |
|---|---|---|
| [`comportamientos-protegidos.md`](comportamientos-protegidos.md) | **Registro vivo** de lo que ya funciona y no puede romperse, con el test que lo cuida | Cada vez que un cambio consolida un comportamiento nuevo |
| `AAAA-MM-DD-<tema>.md` | **Análisis de impacto** de un cambio concreto | Uno por sesión que modifique código |

## Reglas

1. **Se escribe antes de editar.** La columna «qué podría romperse» se llena al empezar; «verificado», al final.
2. **Va en el mismo commit** que el cambio ([`CLAUDE.md`](../../CLAUDE.md), «Project memory»).
3. **Cada fila apunta a un `CP-nnn`.** Si el comportamiento no estaba registrado, se añade primero.
4. **Riesgo honesto.** «Sin impacto» en todas las filas casi nunca es cierto.
5. **La verificación dice qué se corrió**: test con nombre, comando con su salida, o pasos manuales.
6. Lo que se **descubre** al analizar se anota aunque no se toque.

> Riesgo **Alto** = toca redacción/secretos, efectos externos, orden o integridad de eventos, o afirmaciones del
> reporte. Una fila en Alto exige test automático, no comprobación manual.

## Cómo añadir un análisis

1. Copia [`PLANTILLA.md`](PLANTILLA.md) a `AAAA-MM-DD-<tema>.md`.
2. Lista lo que vas a tocar y quién más lo usa (con `grep`, no de memoria).
3. Busca los `CP-nnn` de esa zona; añade los que falten.
4. Riesgo + mitigación **antes** de programar; verificación al terminar.
5. Añade la fila al índice y enlaza el análisis desde la bitácora en [`../sesiones/`](../sesiones/README.md).

## Índice de análisis

| Fecha | Cambio | Comportamientos tocados | Resultado |
|---|---|---|---|
| 2026-11-22 | [Fase 5: adaptador Pydantic AI, puente OTel y benchmark FCRB](2026-11-22-e-fase-5-adaptador-y-benchmark.md) | CP-001…CP-039 (sin regresión) · CP-040…CP-046 (nuevos) | Verificado: 219 tests + ruff + mypy strict; 9 mutaciones del producto detectadas por el benchmark |
| 2026-11-21 | [Fase 4: paquete de evidencia y verificador offline](2026-11-21-d-fase-4-evidencia.md) | CP-001…CP-032 (sin regresión) · CP-033…CP-039 (nuevos) | Verificado: 178 tests + ruff + mypy strict; 8 mutaciones detectadas |
| 2026-11-21 | [Fase 3: ramas, intervención, política y comparación](2026-11-21-c-fase-3-ramas.md) | CP-001…CP-025 (sin regresión) · CP-026…CP-032 (nuevos) | Verificado: 155 tests + ruff + mypy strict; 6 mutaciones detectadas (1 tras un test nuevo) |
| 2026-11-21 | [Publicación en GitHub y Fase 2 (replay)](2026-11-21-b-publicacion-y-fase-2.md) | CP-001…CP-021 (sin regresión) · CP-022…CP-025 (nuevos) | Verificado: 138 tests + ruff + mypy strict; 3 mutaciones de replay detectadas |
| 2026-11-21 | [Arranque: Fase 0 (cimientos) y Fase 1 (grabador local)](2026-11-21-arranque-fase-0-y-1.md) | CP-001…CP-021 (todos nuevos) | Verificado: 123 tests + ruff + mypy strict en verde; 11 mutaciones detectadas |
