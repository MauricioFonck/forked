# Plantilla — Ficha de archivo Python

> **Navegación:** [← Catálogo de plantillas](README.md) · [Plantilla de contexto](plantilla-modulo.md) · [Memoria FORKED](../README.md)
>
> Copia a `contexto/modulos/<contexto>/<archivo>.md` y enlázala desde el README del contexto.

# `src/forked/<ruta>/<archivo>.py`

| | |
|---|---|
| **Capa** | dominio · aplicación · puerto · adaptador de entrada · adaptador de salida · bootstrap |
| **Contexto** | `<contexto>` |
| **Importa** | (lista corta; debe respetar la regla de dependencias) |
| **Lo usan** | (buscar con `grep`, no de memoria) |

## Propósito
Qué hace y por qué existe como archivo separado.

## API pública

| Símbolo | Tipo | Contrato |
|---|---|---|
| `Nombre` | clase / función / enum | Entradas, salida, errores (`code`) |

## Invariantes y errores
- Qué valida, qué lanza y cuándo.

## Decisiones y trampas
- Por qué está escrito así; qué alternativa se descartó; ADR relacionado.

## Tests
- Archivo de test y casos que lo cubren; `CP-nnn` relacionados.
