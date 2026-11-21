# `sesiones/` — Bitácora de sesiones de IA

↑ [Memoria central](../README.md)

> Qué se hizo, qué se tocó y qué quedó pendiente en **cada sesión** de trabajo de una IA (Claude Code u otro LLM) sobre
> este repositorio. Una sesión sin bitácora es una sesión que hay que reconstruir leyendo `git log` y adivinando.

## Para qué existe

El `git log` dice **qué** cambió; los documentos de `contexto/` dicen **cómo funciona** lo que quedó. Ninguno dice *qué
se pidió*, *qué se descartó*, *qué se probó y cómo*, ni *qué quedó a medias*. Eso vive aquí. Sirve para retomar una
tarea, auditar lo que hizo una IA sin releer todo el diff y correlacionar un fallo nuevo con la sesión que tocó esa zona
(junto con [`../impacto/`](../impacto/README.md)).

## Reglas

1. **Una sesión = un archivo** `AAAA-MM-DD-<slug>.md`. Varias el mismo día: sufijo corto (`-b`, el tema).
2. Se escribe **durante** la sesión y se cierra al final, en el **mismo commit** que el código.
3. Se registra **todo lo modificado**, también la documentación, con ruta.
4. Se registra **lo que NO se hizo**: pendientes, decisiones para el dueño, bloqueos.
5. Fechas siempre absolutas (`2026-11-21`, no «hoy»).
6. Un fallo no trivial va a [`../errores/`](../errores/README.md) y aquí solo se enlaza; una regla general, a un
   [ADR](../forked/decisiones-arquitectura/README.md). No se duplica: se enlaza.
7. Toda sesión que toque código enlaza su **análisis de impacto**. Sin análisis, no hay sesión cerrada.

## Cómo añadir una sesión

1. Copia [`PLANTILLA.md`](PLANTILLA.md) con el nombre `AAAA-MM-DD-<slug>.md`.
2. Rellena las secciones conforme avanzas; «Cómo verificar» con los comandos **que de verdad corriste**.
3. Añade la fila al índice (la más reciente **arriba**). *Un archivo que no está en ningún índice no existe.*

## Índice

| Fecha | Sesión | Rama | Áreas | Impacto | Fallos |
|---|---|---|---|---|---|
| 2026-11-21 | [Publicación en GitHub y Fase 2 (replay)](2026-11-21-b-publicacion-y-fase-2.md) | `main` | GitHub, replay, SDK, CLI, CI | [2026-11-21 (b)](../impacto/2026-11-21-b-publicacion-y-fase-2.md) | ninguna |
| 2026-11-21 | [Arranque del proyecto: memoria `contexto/`, revisión de preparación, Fase 0 y Fase 1](2026-11-21-arranque-fase-0-y-1.md) | `main` | todo el repositorio | [2026-11-21](../impacto/2026-11-21-arranque-fase-0-y-1.md) | [E-001](../errores/errores/E-001-el-guardian-del-grafo-no-veia-mayusculas-en-windows.md) |
