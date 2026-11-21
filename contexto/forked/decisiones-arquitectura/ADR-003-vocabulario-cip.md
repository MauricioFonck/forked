# ADR-003 — Un solo vocabulario: el del CIP (2026-11-21)

↑ [Índice de ADR](README.md)

- **Contexto.** La [revisión de preparación](../../revisiones/2026-11-21-revision-de-preparacion.md) encontró tres
  vocabularios que no coinciden:
  1. **Efectos:** FR-009 (`docs/04`) dice `read, write, external, local, unknown`; el CIP §6.5 define seis clases
     (`PURE_LOCAL`, `RECORDED_READ`, `EXTERNAL_READ`, `EXTERNAL_WRITE`, `LOCAL_WRITE`, `UNKNOWN`).
  2. **Afirmaciones:** `CLAUDE.md` usa tres niveles (`descriptive`, `conditional`, `unsupported`); el CIP §6.7 y
     `docs/02` §2.6 usan cuatro (`OBSERVATIONAL`, `CONTROLLED_COMPARISON`, `CONDITIONAL_CAUSAL`, `UNSUPPORTED`).
  3. **Mayúsculas:** el CIP escribe `VERIFIED` en §6.6 pero `"status": "verified"` en su ejemplo JSON.
- **Decisión.**
  - Manda el **CIP**: seis clases de efecto y cuatro niveles de afirmación.
  - Mapeo con `CLAUDE.md`: `descriptive` = `observational` **o** `controlled_comparison`; `conditional` =
    `conditional_causal`; `unsupported` = `unsupported`.
  - En código son `StrEnum` con **valor serializado en minúscula** (`external_write`, `verified`); la documentación
    puede escribirlos en mayúscula como nombres.
  - La **declaración** de un invariante (qué y cómo se verifica) va separada de su **resultado** (`verified/violated/unknown`
    + referencia a evidencia). El ejemplo del CIP los mezcla; la implementación de la Fase 3 no.
- **Refina.** FR-009 y la lista de niveles de `CLAUDE.md` (que sigue siendo válida vía el mapeo).
- **Consecuencias.** Un solo conjunto de enums en `domain/`; los reportes usan los nombres del CIP. Hoy está implementado
  `EffectClass`; niveles de afirmación e invariantes llegan con la Fase 3.
