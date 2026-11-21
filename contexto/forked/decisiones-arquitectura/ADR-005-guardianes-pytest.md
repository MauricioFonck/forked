# ADR-005 — Las reglas estructurales se hacen cumplir con guardianes de pytest (2026-11-21)

↑ [Índice de ADR](README.md)

- **Contexto.** ADR-001 pide comprobar la dirección de dependencias en CI «donde sea práctico» y sugiere import-linter.
  Además hay otras reglas que nadie recuerda a mano: que `spec/` coincida con el código y que `contexto/` no tenga
  enlaces rotos ni documentos huérfanos (lección heredada de la memoria de NextVent).
- **Decisión.** Tres **guardianes** en `tests/guardians/`, que corren con el resto de la suite:
  1. `test_dependency_rule.py` — parsea el AST: el dominio solo importa la biblioteca estándar y `forked.domain`; la
     aplicación no importa frameworks ni adaptadores; los adaptadores de salida concretos solo se importan desde
     `bootstrap` (o desde otros adaptadores de salida). Prohíbe imports relativos.
  2. `test_published_schema.py` — `spec/cip/v0.1/*.schema.json` es idéntico a lo que genera el código; los fixtures
     dorados se leen y hacen ida y vuelta sin cambios.
  3. `test_context_graph.py` — todo enlace relativo de `contexto/` resuelve (con mayúsculas exactas) y todo `.md` es
     alcanzable desde `contexto/README.md`; toda carpeta de spec está indexada.
- **Alternativas.** import-linter (dependencia y configuración extra para una regla que un AST cubre en 90 líneas) ·
  revisión manual (no escala y falla en silencio).
- **Consecuencias.** Un guardián muerde: se demostró con mutaciones el 2026-11-21
  ([bitácora](../../sesiones/2026-11-21-arranque-fase-0-y-1.md#6-cómo-verificar)). Una excepción se agrega en el propio
  guardián con su motivo en la misma línea; una excepción de arquitectura requiere ADR.
