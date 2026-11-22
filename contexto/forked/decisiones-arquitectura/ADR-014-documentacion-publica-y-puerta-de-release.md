# ADR-014 — Documentación pública verificada por tests y puerta de release

↑ [Índice de ADR](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-22 |
| **Estado** | Vigente |
| **Refina** | `docs/09` Fase 6, `docs/10` (gobierno y comunidad), [ADR-013](ADR-013-framework-puente-otel-y-benchmark.md), [arte previo](../../investigacion/arte-previo.md) |

## Contexto

La Fase 6 pide documentación («sitio o Markdown bien organizado»), repositorio de ejemplos, guía de contribución,
plantillas, notas de versión y feedback externo. Ya existían CONTRIBUTING, SECURITY, plantillas y gobierno (adelantados
en la Fase 0). Los riesgos propios de una alfa pública son: documentación que miente o se pudre, promesas de novedad
sin respaldo, y publicar algo que luego no se puede retirar.

## Decisión

1. **Dos conjuntos de documentos.** `docs/guide/` (usuario, **comportamiento actual**, inglés) y `docs/01…14` (propuesta
   y razones). Si difieren, manda la guía para lo que el software hace hoy (`docs/README.md` lo dice).
2. **Markdown, sin generador de sitio.** GitHub lo renderiza, no añade dependencias ni infraestructura; un sitio puede
   venir cuando haya una necesidad medida.
3. **La documentación se prueba** (`tests/guardians/test_public_docs.py`, 44 tests): cada comando de la CLI está en
   la referencia y nada documentado es inventado; los enlaces relativos del README y de las páginas de usuario
   resuelven; todo `forked <comando>` mencionado existe; los fragmentos de Python de la guía al menos parsean; **no hay
   palabras de novedad o superlativos** y el README conserva el aviso de «no es una revisión de arte previo».
4. **Los ejemplos se prueban** (`tests/acceptance/test_examples.py` y pasos de CI): lo primero que ejecuta un recién
   llegado no puede romperse en silencio.
5. **El paquete se prueba instalado**: CI construye la rueda y la ejecuta en un entorno aislado **sin el repositorio**.
   El sdist se adelgazó (2,1 MB → 116 KB: solo fuente, tests, esquemas, ejemplos y benchmark).
6. **El adaptador sin su extra da un error accionable** (`pip install 'forked-runtime[pydantic-ai]'`), no un
   `ModuleNotFoundError`.
7. **Canal de feedback con un objetivo concreto:** plantilla `reproduction_report` (pregunta si quien reporta es
   independiente, porque eso es lo que el gate de `docs/08` §8.6 necesita), guía `06-reproducing-and-reviewing` y una
   sección «dónde ayudar» en CONTRIBUTING. Etiquetas `reproduction` y `proposal` creadas (la segunda no existía y la
   plantilla de la Fase 0 la referenciaba en vano).
8. **La comparación del README declara lo que es:** categorías generalizadas, no una revisión de arte previo; «❌» =
   «no es una función central de la categoría», no «ninguna herramienta lo hace».
9. **Puerta de release: NO se etiqueta, no se publica en PyPI y no se crea el GitHub Release sin decisión del dueño.**
   Las notas de versión quedan como *borrador*. Motivos: es público y difícil de retirar (un nombre en PyPI no se
   reutiliza), la revisión de arte previo sigue abierta y el benchmark no tiene reproducción independiente.

## Alternativas descartadas

- **Sitio con MkDocs/Docusaurus** — dependencia y mantenimiento sin necesidad medida.
- **Documentar solo en el README** — mezcla guía de usuario con propuesta y se vuelve enorme.
- **Generar la referencia de la CLI automáticamente** — oculta cambios de comportamiento; preferimos que el test
  obligue a *leerla* cuando la CLI cambia.
- **Publicar la alfa ya** — ver el punto 9.
- **Habilitar GitHub Discussions** — ajuste del repositorio del dueño; se propone, no se hace.

## Consecuencias

- Cambiar la CLI sin actualizar la referencia rompe el test (es la intención).
- Quien quiera usar la palabra «novedoso» debe antes cerrar el arte previo y ajustar el guardián: es una puerta
  deliberada, no un olvido.
- Un lector externo tiene un camino completo: instalar desde el código fuente, ejecutar, reproducir y reportar.
- La instalación sigue siendo desde el código fuente hasta que el dueño decida publicar.
