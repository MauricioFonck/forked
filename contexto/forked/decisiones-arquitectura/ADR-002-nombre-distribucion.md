# ADR-002 — Distribución `forked-runtime`, import `forked` (2026-11-21)

↑ [Índice de ADR](README.md)

- **Contexto.** El nombre `forked` **ya existe en PyPI** (comprobado el 2026-11-21: `https://pypi.org/pypi/forked/json`
  responde 200). `forked-runtime`, `forked-cip` y `forkedlab` respondían 404. [`docs/12`](../../../docs/12-decisions-and-open-questions.md)
  §12.4 exige comprobar nombres antes del lanzamiento.
- **Decisión.** El paquete se distribuye como **`forked-runtime`**; el import y el comando siguen siendo **`forked`**
  (`import forked`, `forked record …`). El repositorio se propone como `forked`.
- **Alternativas.** `forked-cip` (ata el paquete al protocolo, que es provisional) · `forkedlab` (suena a producto
  hospedado) · renombrar el proyecto (prematuro: el nombre aún está sujeto a revisión de marca).
- **Consecuencias.** Si alguien instala a la vez el paquete ajeno `forked`, los imports pueden chocar; se documenta y se
  revisa antes de publicar en PyPI. **No se ha publicado nada en PyPI**: reservar el nombre es una decisión del dueño.
- **Revisar cuando.** Termine la revisión de marca/nombre de [`docs/12`](../../../docs/12-decisions-and-open-questions.md) §12.4.
