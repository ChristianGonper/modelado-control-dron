# Simulador Multirotor

Base inicial del simulador modular para un dron multirotor. Esta primera fase deja preparado el esqueleto del proyecto, el punto de entrada único y los contratos de datos compartidos que usarán la dinámica, el control, las trayectorias y la telemetría.

## Quick Start

1. Sincroniza el entorno con `uv sync`.
2. Lanza la ejecución mínima con `uv run multirotor-sim`.
3. Ejecuta los tests con `uv run pytest`.
4. Genera análisis estáticos con `uv run multirotor-sim --analysis-dir analysis_outputs`.

## Estructura

- `src/simulador_multirotor/core`: contratos de datos compartidos.
- `src/simulador_multirotor/dynamics`: integración 6DOF mínima.
- `src/simulador_multirotor/control`: espacio para controladores.
- `src/simulador_multirotor/trajectories`: espacio para trayectorias y referencias.
- `src/simulador_multirotor/scenarios`: espacio para escenarios.
- `src/simulador_multirotor/telemetry`: espacio para telemetría y exportación.
- `src/simulador_multirotor/visualization`: análisis 2D/3D sobre telemetría persistida.
- `src/simulador_multirotor/runner.py`: orquestación mínima extremo a extremo.

## Decisiones de arquitectura

- Los contratos compartidos viven en `core/contracts.py` para evitar dependencias circulares entre módulos.
- Los modelos base usan `dataclasses` del estándar para mantener la fase 1 sin dependencias de validación externas.
- El comando `multirotor-sim` es el punto de entrada único para la ejecución mínima.
- La visualización lee telemetría exportada y genera PNG estáticos sin acoplarse al runner.

## Documentación

- [Estado actual del simulador](docs/estado_actual_simulador.md)
- [Backlog técnico recomendado](docs/backlog_tecnico.md)
- [Puntos de extensión](docs/extension-points.md)
- [Decisiones](docs/decisions/): ADRs de arquitectura y decisiones de diseño por fase
