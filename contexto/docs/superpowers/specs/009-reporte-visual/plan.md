# Spec 009 · Plan

[Spec](spec.md) · [Tareas](tasks.md) · [Bitácora](../../../../sesiones/2026-11-22-h-reporte-visual.md)

1. Renderizador puro `html_report.py` (escape, CSP, SVG del fork) + `report.css` como dato del paquete.
2. Comando `forked report` (exporta y verifica la evidencia en un directorio temporal; `--open`).
3. Tests de seguridad (XSS, CSP), contenido, determinismo y errores; mutaciones sobre los controles.
4. **Mirar el resultado de verdad** (capturas con Edge sin interfaz) y corregir lo visual.
5. Documentar (guía, README, CHANGELOG, ADR) y probar la rueda aislada.
