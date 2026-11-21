# ADR-004 — Persistencia de la Fase 1: JSONL + `run.json` atómico; SQLite diferido (2026-11-21)

↑ [Índice de ADR](README.md)

- **Contexto.** D-003 prevé «JSONL + índice SQLite». El alcance del MVP lista SQLite, pero la Fase 1 dice «SQLite si
  hace falta». Las únicas consultas de la Fase 1 son: leer un run, leer sus metadatos y listar runs.
- **Decisión.** Por run, una carpeta `runs/<run_id>/` con:
  - `events.jsonl`: append-only, una línea por evento, LF, `flush` por evento. **Es la fuente canónica**.
  - `run.json`: metadatos (estado, adaptador, entorno, `next_sequence`). Se reemplaza **atómicamente** (escribir
    temporal + `fsync` + `os.replace`).
  - Listar runs recorre `runs/`. **Sin SQLite** hasta que una consulta lo justifique con una medición.
- **Recuperación ante caída.** Si el proceso muere: `run.json` queda en `recording` ⇒ la inspección lo reporta
  `incomplete`; una última línea sin `\n` ⇒ `CorruptRecording` con su número de línea. `next_sequence` distinto del
  número de líneas ⇒ evidencia faltante explícita. Nunca se repara ni se salta en silencio.
- **Alternativas.** SQLite desde ya (una dependencia de esquema y migraciones sin consulta que la pague) · un solo
  archivo por run con cabecera (mezcla datos mutables con el log append-only).
- **Consecuencias.** Listar es O(runs) en disco: aceptable para el MVP local. El `fsync` por evento no se hace (costo en
  Windows); se acepta perder la cola de eventos en una caída del SO, y eso se **reporta**, no se oculta.
- **Revisar cuando.** Haya consultas por rama/linaje (Fase 3) o listados lentos medidos.
