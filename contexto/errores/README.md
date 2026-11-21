# `errores/` — Catálogo de fallos del proyecto

↑ [Memoria central](../README.md)

> Qué salió mal, **por qué** salió mal, y qué concepto técnico no se estaba aplicando cuando pasó. No es una lista de
> tickets: es la memoria de los errores para no repetirlos.

Un fallo arreglado y no escrito se vuelve a cometer, normalmente en otro contexto y con la misma causa raíz. Por eso cada
ficha insiste menos en el parche y más en **el concepto que se ignoró**.

## Las dos categorías

| | **Bugs** (`bugs/B-nnn-…`) | **Errores** (`errores/E-nnn-…`) |
|---|---|---|
| **Qué es** | FORKED hace algo incorrecto: un evento perdido, un reporte que exagera, un secreto en disco | El entorno o la herramienta fallan: no instala, no compila, CI rojo por plataforma |
| **Lo sufre** | Quien confía en la evidencia, muchas veces **sin darse cuenta** | Quien desarrolla, y se entera al instante |
| **Se arregla en** | Dominio, aplicación, adaptadores, formato | `pyproject`, CI, scripts, configuración |
| **Se previene con** | Tests de contrato, de seguridad y de regresión | Lock, checks de entorno, documentación operativa |
| **Gravedad típica** | Alta y silenciosa: corrompe conclusiones | Ruidosa pero contenida |

> Regla para clasificar: **si el fallo puede cambiar lo que un usuario cree sobre un experimento, es un bug.**

La ficha se escribe si costó más de una sesión, si la causa no era la que parecía, si ya se había cometido en otro
contexto o si el fallo era **silencioso**. Plantilla: [`PLANTILLA.md`](PLANTILLA.md). La carpeta `bugs/` se crea con la
primera ficha de producto.

## Índice — Bugs

| # | Título | Contexto | Concepto que faltó |
|---|---|---|---|
| — | Ninguno todavía (proyecto iniciado el 2026-11-21) | — | — |

## Índice — Errores de entorno

| # | Título | Área | Concepto que faltó |
|---|---|---|---|
| [E-001](errores/E-001-el-guardian-del-grafo-no-veia-mayusculas-en-windows.md) | El guardián del grafo daba por buenos enlaces con mayúsculas equivocadas en Windows | guardianes | Normalizar antes de validar destruye la evidencia (`resolve()` corrige mayúsculas) |
