# Impacto AAAA-MM-DD — <cambio en una línea>

↑ [Índice de impacto](README.md)

| | |
|---|---|
| **Fecha** | AAAA-MM-DD |
| **Sesión** | `../sesiones/AAAA-MM-DD-<tema>.md` |
| **Rama / commits** | `rama` · `hash` |
| **Estado** | Análisis previo · Verificado · Regresión detectada (→ ficha `B-0XX`) |

## 1. Qué se va a tocar

Archivos, contratos (puertos, formato en disco, CLI, esquema publicado) y **quién más los usa** (búscalo con `grep`).

| Zona | Archivo / contrato | Otros llamadores o consumidores |
|---|---|---|
| … | … | … |

## 2. Qué funciona hoy y qué le podría pasar

| Id | Comportamiento que funciona hoy | Qué le podría pasar con este cambio | Riesgo | Mitigación |
|---|---|---|---|---|
| CP-xxx | … | … | Bajo · Medio · Alto | … |

## 3. Lo que se descubrió al analizar

Llamadores olvidados, defaults peligrosos, contratos que dos contextos leen distinto.

## 4. Verificación posterior

| Id | Cómo se verificó | Resultado |
|---|---|---|
| CP-xxx | `comando` / test `nombre` / mutación | OK · FALLÓ (→ qué se hizo) |

## 5. Comportamientos nuevos que pasan a protegidos

Los que este cambio introduce, añadidos al registro con id nuevo.
