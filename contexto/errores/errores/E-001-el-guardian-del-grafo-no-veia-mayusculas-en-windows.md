# E-001 — El guardián del grafo daba por buenos enlaces con mayúsculas equivocadas en Windows

↑ [Catálogo de fallos](../README.md)

| | |
|---|---|
| **Tipo** | Error de entorno/herramienta |
| **Contexto** | `tests/guardians/test_context_graph.py` |
| **Detectado por** | mutación (2026-11-21) |
| **Arreglado en** | commit inicial del repositorio |
| **Estado** | Cerrado |

## 1. Síntoma

Al probar el guardián con un enlace `[y](../Modulos/README.md)` (la carpeta real es `modulos/`), el guardián seguía en
verde en Windows. Fallo **silencioso**: en la máquina del dueño todo pasa; en el CI de Linux, o para cualquier lector en
GitHub, el enlace está roto.

## 2. A qué se debía

El guardián resolvía cada destino con `Path.resolve()` y luego comparaba nombres contra el listado del directorio. En
Windows, `resolve()` devuelve la ruta **con las mayúsculas reales del disco**, así que la comparación siempre coincidía:
el dato que había que comprobar se corregía antes de comprobarlo. Evidencia: con `normpath` en lugar de `resolve()`, la
misma mutación produce `errores/README.md -> ../Modulos/README.md` en rojo.

## 3. Conceptos técnicos en juego

### Lo que no se tuvo en cuenta

**Normalizar antes de validar destruye la evidencia.** `resolve()` canonicaliza (mayúsculas, symlinks, `..`) y en un
sistema de archivos insensible a mayúsculas oculta exactamente el defecto que se quería detectar.

### Lo que se aplicó al arreglarlo

Se normaliza solo la sintaxis (`os.path.normpath`, que colapsa `..` sin tocar mayúsculas) y se recorre cada componente
desde la raíz del repositorio comparándolo con `iterdir()`. Costo: un listado de directorio por componente, irrelevante
para ~60 documentos.

## 4. Cómo se solucionó

`tests/guardians/test_context_graph.py`: `_links()` usa `normpath`; `_exists_exact_case()` recorre componente a
componente desde `ROOT`; la alcanzabilidad compara rutas sin `resolve()`.

## 5. Cómo evitar que se repita

- **Regla accionable:** en un validador, no canonicalices la entrada con funciones que «arreglan» lo que validas.
- **Red de seguridad:** CP-021 y la mutación documentada en la [bitácora](../../sesiones/2026-11-21-arranque-fase-0-y-1.md#6-cómo-verificar).
  El CI corre además en Linux, sensible a mayúsculas.
- **Dónde más aplica:** el futuro verificador de paquetes de evidencia (Fase 4) y la extracción de archivos: comprobar
  rutas **antes** de resolverlas (path traversal y symlinks).
