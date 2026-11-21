# Hipótesis de investigación

↑ [Investigación](README.md) · [Memoria central](../README.md)

Estados: **abierta** (sin evidencia) · **con soporte parcial** (hay mecanismo, falta medición comparativa) ·
**soportada** (medida contra línea base, reproducida) · **refutada**.

| Id | Hipótesis | Estado al 2026-11-21 | Evidencia / qué falta |
|---|---|---|---|
| H1 | Registrar procedencia y huella de entorno mejora el diagnóstico de replays divergentes frente a logs sin estructura | Abierta | Existe la huella de entorno y la lista de hechos faltantes (CP-011). Falta: escenario FCRB 7 y comparación contra logs planos |
| H2 | Un modelo tipado de intervención e invariantes detecta comparaciones inválidas mejor que comparar salidas | Abierta | Fase 3 |
| H3 | Default-deny + observaciones grabadas reduce escrituras externas duplicadas en replay | Abierta | La clase de efecto ya se graba por herramienta; la política es Fase 2. Falta: escenario FCRB 4 |
| H4 | Un paquete de evidencia portable permite a un verificador independiente validar integridad y condiciones declaradas | Abierta | Fase 4 |
| H5 | Un contrato de adaptador común soporta varios frameworks sin imponer un runtime | Abierta | Un solo adaptador (juguete). Falta: escenario FCRB 10 con dos adaptadores |

## Criterios de falsación (se revisan o abandonan las afirmaciones si…)

- el sobrecosto de metadatos vuelve inutilizable la captura para la carga objetivo;
- el runtime no distingue con fiabilidad observaciones grabadas de operaciones con efectos;
- los invariantes no se pueden comprobar o reportar honestamente;
- los adaptadores requieren semántica específica del framework que el protocolo no puede representar;
- el benchmark no muestra mejora significativa frente a logging de eventos simple y herramientas de replay existentes.

## Frontera del lenguaje causal

Diferencia observada ≠ comparación controlada ≠ estimación causal condicional. Un hash prueba integridad de bytes, no
verdad causal. Vocabulario: [ADR-003](../forked/decisiones-arquitectura/ADR-003-vocabulario-cip.md).
