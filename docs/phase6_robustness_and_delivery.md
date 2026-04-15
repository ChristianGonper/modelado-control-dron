# Phase 6 - Robustez y entrega

## Alcance

Esta fase separa dos preguntas distintas:

- conclusiones dentro de distribución sobre la batería principal
- conclusiones exploratorias sobre robustez OOD

La batería OOD se ejecuta con `src/simulador_multirotor/robustness.py` y se persiste aparte del benchmark principal.

## Conclusiones Dentro De Distribución

Las conclusiones ID deben leerse solo desde el artefacto principal generado por `generate_phase5_report(...)`.

- La comparación principal sigue siendo clásico vs `mlp` vs `gru` vs `lstm`.
- La arquitectura seleccionada se toma del artefacto `selection.json`.
- La regla de selección sigue siendo determinista y ponderada: precisión, suavidad, robustez e inferencia.

## Conclusiones OOD

La batería OOD vive fuera del circuito de selección.

- Se ejecuta con `run_ood_robustness_benchmark(...)`.
- Se reporta con `generate_ood_report(...)`.
- No actualiza hiperparámetros, no reemplaza el benchmark principal y no se usa para escoger la arquitectura final.

## Límites Metodológicos

El trabajo de esta fase sigue siendo imitation learning sobre el controlador experto disponible.

- La política imita demostraciones del controlador clásico; no equivale a aprendizaje por refuerzo.
- La política ve `observed_state`, no verdad física privilegiada.
- `true_state` se usa para evaluación, no para inferencia.
- La robustez OOD diagnostica degradación bajo condiciones más duras o no vistas, pero no justifica conclusiones sim-to-real.

## Paquete De Reproducibilidad

Artefactos clave:

- Checkpoints: `mlp.pt`, `gru.pt`, `lstm.pt`
- Benchmark principal: `benchmark.json`
- Reporte principal: `report.md`
- Selección determinista: `selection.json`
- Batería OOD: `ood-benchmark.json`
- Reporte OOD: `ood_report.md`

Configuración fija:

- Feature mode: `observation_plus_tracking_errors`
- Ventana MLP: `30`
- Ventana GRU: `100`
- Ventana LSTM: `150`
- Rutas de escenarios OOD: `build_ood_robustness_scenarios()`

Rerun path recomendado:

```python
from pathlib import Path

from simulador_multirotor.benchmark import run_homogeneous_neural_benchmark, run_ood_robustness_benchmark
from simulador_multirotor.reporting import generate_ood_report, generate_phase5_report
from simulador_multirotor.robustness import build_ood_robustness_scenarios
from simulador_multirotor.scenarios import build_minimal_scenario

# Reuse the same checkpoints that were produced during Phase 3 and Phase 4.
# Then rerun the main benchmark and the OOD battery into separate output dirs.
main_output = Path("outputs/phase5")
ood_output = Path("outputs/phase6/ood")
scenarios = build_ood_robustness_scenarios()
```

## Selección Final

La arquitectura final es la que escriba `selection.json` en el reporte principal.

La razón de la elección es la misma que define la regla reproducible ya implementada: menor puntuación ponderada entre precisión, suavidad, robustez y coste de inferencia.

