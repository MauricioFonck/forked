# Plantilla — README de contexto acotado

> **Navegación:** [← Catálogo de plantillas](README.md) · [Contextos](../modulos/README.md) · [Memoria FORKED](../README.md)
>
> Copia a `contexto/modulos/<contexto>/README.md`. Borra las líneas de ayuda al instanciar.

# Contexto `<nombre>` — <nombre en docs/05>

↑ [Contextos](../modulos/README.md) · [Memoria central](../README.md)

## Responsabilidad
Qué parte del experimento cubre (1–3 frases) y qué UC/FR de `docs/04` implementa.

## Qué problema resuelve
…

## Archivos

| Archivo | Capa | Responsabilidad |
|---|---|---|
| `domain/<contexto>/<x>.py` | Dominio | … |
| `application/commands/<x>.py` | Aplicación | … |
| `application/ports/…` | Puertos | … |
| `adapters/outbound/…` | Adaptador | … |

## Puertos que usa / implementa
- `<Puerto>` — quién lo implementa y qué contrato cumple (`tests/contract/…`).

## Reglas de negocio clave
- Invariantes, transiciones de estado, qué falla cerrado.

## Garantías y límites
- Qué garantiza **y qué no** (lenguaje honesto: sin «determinista» ni «causal» sin evidencia).

## Consumido por
- …

## Tests que lo cuidan
- Archivos de test y `CP-nnn` de [comportamientos protegidos](../impacto/comportamientos-protegidos.md).

## 📌 Pendiente de pasada profunda
- [ ] Ficha por archivo con [`plantilla-archivo.md`](plantilla-archivo.md).
