# ADR-017 — Reporte visual como un único archivo HTML autocontenido

↑ [Índice de ADR](README.md)

| | |
|---|---|
| **Fecha** | 2026-11-22 |
| **Estado** | Vigente |
| **Refina** | `docs/09` (P2 «Studio prototype»: esto **no** es ese Studio), [ADR-014](ADR-014-documentacion-publica-y-puerta-de-release.md), `docs/07` (privacidad) |

## Contexto

Todo se veía solo por consola. El dueño pidió «verlo visualmente». Lo grabado es **no confiable** (nombres de herramienta,
argumentos, resultados y mensajes de error vienen del flujo del usuario) y el proyecto es *local-first*: sin servicios ni
dependencias de red.

## Decisión

1. **`forked report RUN [BRANCH] [--out] [--open]`** escribe **un solo archivo HTML**. Con una rama añade el diagrama del
   fork (línea base arriba, rama abajo, cada paso coloreado por lo que pasó: reproducido, intervenido, denegado o ejecutado),
   la tabla de pasos, los cambios de resultado, las cinco invariantes con lo que se comprobó, el nivel de afirmación y un
   paquete de evidencia **exportado y verificado en el momento**.
2. **Sin JavaScript, sin recursos externos, con CSP estricta** (`default-src 'none'; style-src 'unsafe-inline'`). Aunque un
   error futuro de escape dejara pasar HTML, el navegador no ejecutaría código ni abriría conexiones.
3. **Todo dato dinámico se escapa** (`html.escape(quote=True)`), también en atributos y en el SVG. La salida es
   **determinista** (sin marcas de tiempo): los mismos runs dan los mismos bytes, y eso se prueba.
4. **Vive en `adapters/inbound/cli/`** (`html_report.py` + `report.css` como dato del paquete). Solo *presenta* DTOs que la
   aplicación ya calculó (`RunReport`, `Comparison`, `VerificationReport`); no decide nada. No puede estar en
   `adapters/outbound` porque la CLI no puede importarlo (regla del guardián).
5. **`--open`** usa `webbrowser` de la biblioteca estándar; sin servidor, sin puerto abierto.
6. **El archivo es una copia de los datos** (ya redactados): se documenta como tal y `forked-report.html` está en
   `.gitignore`.

## Alternativas descartadas

- **Servidor local con interfaz web** — abre un puerto, añade superficie de ataque y dependencias; es el «Studio» de
  `docs/09`, aplazado hasta que haya necesidad medida.
- **Bibliotecas de gráficos en JavaScript** — dependencias y scripts, incompatibles con la CSP.
- **Graphviz u otros binarios** — requieren instalar software aparte.
- **Informe en Markdown** — no permite el diagrama ni colores; ya existe para el benchmark.
- **Imágenes PNG** — no son accesibles ni seleccionables.

## Consecuencias

- Sin interactividad (solo `<details>`), un par línea base/rama por informe y una vista por archivo.
- El aspecto se comprobó **a ojo** con capturas de Edge sin interfaz (se corrigieron tres defectos: SVG demasiado grande,
  números de paso tapados por la línea punteada, tabla desbordada); esa revisión visual **no** está automatizada en CI.
- Los tests vigilan lo que sí es automatizable: escape (XSS), CSP, ausencia de scripts y de recursos externos,
  determinismo, contenido (decisiones, invariantes, evidencia) y errores.
