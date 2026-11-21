# Versionado del esquema

↑ [Protocolo](README.md) · [Memoria central](../README.md)

- **SemVer** (`MAJOR.MINOR.PATCH`), independiente de la versión del paquete. Hoy: **0.1.0**
  (`domain/shared/schema.py`, `EVENT_SCHEMA_VERSION`).
- Un lector **rechaza** una versión mayor no soportada (`SUPPORTED_MAJOR_VERSIONS = {0}`) antes de validar campos.
- Una versión menor nueva solo puede **agregar campos opcionales**. Por eso el lector ignora campos desconocidos
  (`extra="ignore"`): un archivo 0.2.0 sigue siendo legible por un lector 0.1.
- Un cambio incompatible exige versión mayor, propuesta escrita y plan de migración
  ([`GOVERNANCE.md`](../../GOVERNANCE.md)).

## Cómo cambiar el esquema

1. Cambiar `EventRecord`/`RunRecord` y el dominio.
2. `uv run python scripts/export_schemas.py` regenera `spec/cip/v0.1/` (o una carpeta nueva para otra versión mayor).
3. **Agregar** fixtures dorados nuevos en `tests/fixtures/events/vX.Y/`. Nunca editar uno publicado: son la prueba de
   compatibilidad hacia atrás.
4. El guardián [`test_published_schema.py`](../../tests/guardians/test_published_schema.py) falla si `spec/` no coincide
   con el código o si un fixture deja de leerse.
