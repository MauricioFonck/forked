# Sesión AAAA-MM-DD — <tema en una línea>

↑ [Bitácora de sesiones](README.md)

| | |
|---|---|
| **Fecha** | AAAA-MM-DD |
| **IA / herramienta** | Claude Code (modelo) · otro LLM |
| **Rama** | `nombre-de-la-rama` |
| **Commits** | `hash1`, `hash2` (o «sin commit: pendiente de revisión») |
| **Análisis de impacto** | `../impacto/AAAA-MM-DD-<slug>.md` |
| **Fichas de fallo** | `B-0XX` · `E-0XX` · ninguna |

## 1. Qué se pidió

Lo que dijo el usuario, en sus términos. Si era ambiguo, la interpretación tomada y por qué.

## 2. Qué se encontró (diagnóstico)

Síntoma → causa real → evidencia (archivo:línea, test, medición).

## 3. Qué se hizo

| Área | Archivo | Cambio | Por qué |
|---|---|---|---|
| dominio | `src/forked/domain/...` | … | … |
| tests | `tests/...` | … | … |
| docs | `contexto/...` | … | … |

## 4. Qué se descartó y por qué

## 5. Qué quedó pendiente / decisiones para el usuario

## 6. Cómo verificar

```bash
uv run pytest      # N passed
```

Si algo no se pudo verificar, dilo aquí.
