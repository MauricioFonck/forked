# <B|E>-00X — <título en una línea, en lenguaje de síntoma, no de solución>

↑ [Catálogo de fallos](README.md)

| | |
|---|---|
| **Tipo** | Bug de producto · Error de entorno/operación |
| **Contexto** | `<runs · effects · replay · … · CI>` |
| **Detectado por** | test · revisión · usuario · mutación · CI |
| **Arreglado en** | `<hash del commit>` |
| **Estado** | Cerrado · Mitigado · Abierto |

## 1. Síntoma

Qué se veía. Si el fallo era **silencioso**, dilo y explica por qué nadie lo notaba.

## 2. A qué se debía

La causa **raíz**, no la primera capa, con la evidencia que lo demostró (test, línea, medición). Si hubo un intento de
arreglo fallido, cuéntalo.

## 3. Conceptos técnicos en juego

### Lo que no se tuvo en cuenta

El concepto o la garantía que se ignoró, con su nombre técnico para que sea buscable.

### Lo que se aplicó al arreglarlo

El concepto correcto, por qué es el correcto aquí y lo que cuesta.

## 4. Cómo se solucionó

El cambio concreto, con rutas de archivo.

## 5. Cómo evitar que se repita

- **Regla accionable** para quien escribe código nuevo.
- **Red de seguridad**: el test o guardián que impide que vuelva en silencio (y su `CP-nnn`). Si no la hay, dilo.
- **Dónde más aplica**: los sitios con la misma forma.
