# ADR-009 — Secuencia contigua desde 0, ids aleatorios, tiempo UTC con zona (2026-11-21)

↑ [Índice de ADR](README.md)

- **Contexto.** El sobre de evento del CIP exige `sequence`, `event_id`, `run_id` y `timestamp` pero no fija base,
  formato ni reloj.
- **Decisión.**
  - **Secuencia:** entero contiguo **desde 0** por run, en el orden del archivo. Solo el agregado `Run` la asigna; un
    borrador inválido no consume número. El **orden lo da la secuencia**, no el tiempo.
  - **Ids:** `run_` / `evt_` + 8–64 caracteres `[0-9a-z]`. En producción, 128 bits aleatorios (`secrets.token_hex(16)`).
    El patrón estricto es también un **control de seguridad**: un `run_id` es nombre de carpeta y `../` es imposible.
  - **Tiempo:** `datetime` con zona obligatoria (UTC en `SystemClock`), serializado RFC 3339. Un timestamp sin zona es
    un evento inválido. Hora e ids llegan por puertos, así los tests son deterministas.
- **Alternativas.** ULID/UUIDv7 ordenables por tiempo (no hacen falta: el orden lo da la secuencia, y un id con tiempo
  embebido filtra cuándo ocurrió algo) · secuencia desde 1 (sin ventaja; 0 coincide con índices de lista).
- **Consecuencias.** `check_sequence` detecta huecos, duplicados, desorden y eventos de otro run; un truncamiento de la
  cola no es un «hueco», por eso la completitud compara además `next_sequence` con las líneas del log.
