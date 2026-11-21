# Política de efectos (objetivo, Fase 2)

↑ [Diagramas](README.md) · [Memoria central](../README.md)

```mermaid
flowchart TD
  A[Operación solicitada en replay o rama] --> B{¿Clase de efecto conocida?}
  B -- no --> X[DENY + reportar unknown]
  B -- sí --> C{Clase}
  C -- recorded_read --> D[REPLAY: devolver resultado grabado]
  C -- external_read --> E{¿Hay respuesta grabada?}
  E -- sí --> D
  E -- no --> X2[DENY: fallo cerrado]
  C -- pure_local --> F[ALLOW en sandbox declarado]
  C -- local_write --> G[ALLOW solo en almacenamiento desechable de la rama]
  C -- external_write --> X3[DENY por defecto]
```

Toda decisión deja un evento de auditoría con versión de política, motivo y alcance. `SIMULATE` existe solo como
decisión **explícita** y queda marcada en la evidencia. Taxonomía: [protocolo](../protocolo/taxonomia-de-efectos.md).
