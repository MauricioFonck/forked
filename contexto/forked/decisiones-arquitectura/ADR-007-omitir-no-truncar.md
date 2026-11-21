# ADR-007 — Payload demasiado grande: omitir con digest, nunca truncar; sobre-redactar antes que filtrar (2026-11-21)

↑ [Índice de ADR](README.md)

- **Contexto.** [`docs/07`](../../../docs/07-security-and-privacy.md) §7.3 pide limitar el tamaño de artefactos y
  redactar antes de persistir, pero no dice qué hacer con un payload que excede el límite ni cómo equilibrar falsos
  positivos de la redacción.
- **Decisión.**
  - **Orden del pipeline:** validar JSON → **redactar** → medir → si excede `max_payload_bytes` (64 KiB por defecto), el
    evento queda `omitted`: `payload = null` y `payload_digest = sha256:` del **contenido ya redactado**.
  - **Nunca truncar.** Un payload truncado parece completo y miente; uno omitido se declara como evidencia faltante.
  - El digest es del contenido redactado porque el digest de un secreto permite confirmar un secreto adivinado.
  - **Sobre-redacción aceptada:** se redacta toda clave cuyo nombre normalizado contenga `password`, `secret`, `token`,
    `apikey`, `authorization`, `cookie`, `credential`, `privatekey`, `accesskey`, `sessionid`, `passwd`, y todo string con
    forma de credencial conocida (`sk-…`, `ghp_…`, `github_pat_…`, `AKIA…`, `xox?-…`, `Bearer …`, PEM). `token_count`
    se redacta: es el costo aceptado.
  - El texto libre que viene de fuera (motivos de fallo) pasa por el mismo pipeline antes de ir a `run.json`.
- **Alternativas.** Truncar (rechazado: miente) · almacenar el payload grande aparte (diferido: contenido direccionable
  llega cuando un test de payloads grandes lo justifique) · redacción solo por lista blanca (más precisa, pero exige
  configuración por adaptador; se puede añadir después).
- **Consecuencias.** La redacción es **best effort** y así se declara en `SECURITY.md`. Un valor sobre-redactado puede
  añadirse a una lista de permitidos en el futuro; un secreto filtrado no se puede «des-filtrar».
