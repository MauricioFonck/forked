# Spec 001 · Cimientos del repositorio (Fase 0)

[Plan](plan.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-21-arranque-fase-0-y-1.md) · [Impacto](../../../../impacto/2026-11-21-arranque-fase-0-y-1.md)

**Fecha:** 2026-11-21 · **Estado:** hecha

## Qué y por qué

Convertir la propuesta en `docs/` en un repositorio que se pueda clonar, instalar, probar y al que se pueda contribuir
sin romper sus reglas: arquitectura hexagonal verificada por máquina, CI multiplataforma, políticas de seguridad y
contribución, y una memoria de ingeniería (`contexto/`) con el mismo método que la de NextVent.

## Criterios de aceptación ([`docs/09`](../../../../../docs/09-roadmap-and-backlog.md), Fase 0)

- [x] Andamiaje de paquete con capas `domain/application/ports/adapters/bootstrap`.
- [x] Decisiones de arquitectura registradas (ADR-001 público + ADR-002…009).
- [x] README sin afirmaciones sin sustento (estado «pre-alpha», qué funciona y qué no).
- [x] Revisión del esquema de evento: [revisión de preparación](../../../../revisiones/2026-11-21-revision-de-preparacion.md).
- [x] Esqueleto de CI.
- [ ] Revisión de arte previo y nombre del protocolo → abierta en [arte previo](../../../../investigacion/arte-previo.md).

## Fuera de alcance

Publicar en PyPI, reservar dominios o marcas, sitio de documentación.
