# Base Operativa De La CLI Neuronal

## Proposito

Este documento fija la base operativa del flujo neuronal para `MLP`, `GRU` y `LSTM` antes de escribir la capa de CLI completa. Su objetivo es dejar por escrito tres cosas:

- que capacidades internas ya existen y pueden reutilizarse
- como debe verse la superficie publica de comandos y argumentos
- que convención de artefactos y metadatos debe seguir cada etapa

La referencia de decisión de alto nivel es [ADR-018](../decisions/ADR-018-neural-cli-foundation-and-artifact-convention.md).

## Inventario De Capacidades Internas Reutilizables

La base actual del repositorio ya cubre el flujo neuronal esencial. Lo que falta no es capacidad algorítmica, sino operabilidad pública.

| Area | Capacidad ya disponible | Archivos y funciones relevantes | Hueco de operabilidad |
| --- | --- | --- | --- |
| Dataset | Contrato cerrado de features y targets; extracción desde telemetría persistida; split por episodios; windowing para `MLP`, `GRU` y `LSTM` | `dataset/contract.py`, `dataset/extract.py`, `dataset/split.py`, `dataset/features.py`, `dataset/windowing.py` | No existe un comando CLI que convierta telemetría en dataset reutilizable ni una salida manifiestada de esa preparación |
| MLP | Entrenamiento reproducible, checkpoint auditable, carga para inferencia y resumen persistido | `control/mlp.py` (`MLPTrainingConfig`, `train_mlp_checkpoint`, `load_mlp_controller`, `dump_checkpoint_summary`) | No existe un comando CLI para entrenar, inspeccionar o empaquetar checkpoints de MLP |
| GRU y LSTM | Entrenamiento reproducible, checkpoint auditable, carga para inferencia y resumen persistido | `control/recurrent.py` (`RecurrentTrainingConfig`, `train_gru_checkpoint`, `train_lstm_checkpoint`, `load_gru_controller`, `load_lstm_controller`, `dump_checkpoint_summary`) | No existe un comando CLI para entrenar o inspeccionar cada arquitectura recurrente por separado |
| Benchmark principal | Comparación baseline vs `MLP`, `GRU` y `LSTM` con trazas y tiempos de inferencia | `benchmark.py` (`run_homogeneous_neural_benchmark`) | No existe un comando CLI que resuelva checkpoints, ejecute la comparativa y guarde un artefacto con convenio estable |
| Benchmark OOD | Batería OOD separada con su propio `scenario_set_key` y persistencia independiente | `benchmark.py` (`run_ood_robustness_benchmark`), `robustness.py` | No existe un comando CLI separado que haga visible la frontera metodológica y la separación de artefactos |
| Reporting | Tabla consolidada, selector reproducible, figuras comparativas y reporte OOD separado | `reporting.py` (`build_consolidated_table_markdown`, `select_best_neural_model`, `generate_phase5_report`, `generate_ood_report`) | No existe un comando CLI que consuma benchmark persistido y emita el paquete de reporte final |
| CLI actual | Entrada funcional para demo, escenario externo y análisis de telemetría | `app.py` | La interfaz pública no expone dataset, entrenamiento, benchmark, inspección ni reporte del flujo neuronal |

### Huecos Reales Frente A La Superficie Publica Actual

Los huecos que sí requieren capa operativa son estos:

1. No hay un grupo de comandos neuronal bajo el comando raíz.
2. No hay separación explícita entre preparación de dataset, entrenamiento individual, entrenamiento comparativo, benchmark principal, benchmark OOD, reporte e inspección.
3. No hay contrato de nombres para directorios y archivos de salida.
4. No hay manifiesto mínimo que diga qué entrada produjo cada artefacto.
5. No hay validación temprana de combinaciones inválidas de argumentos a nivel de CLI.

La lógica interna existente se reutiliza; lo que se añade es adaptación ligera para exposición pública, resolución de rutas y persistencia de metadatos de ejecución.

## Superficie CLI Propuesta

La superficie pública recomendada vive bajo el comando raíz del simulador y agrupa todo el flujo neuronal en un namespace estable:

```text
multirotor-sim neural <subcomando> [opciones]
```

### Subcomandos

| Subcomando | Propósito | Entrada principal | Salida principal |
| --- | --- | --- | --- |
| `neural dataset prepare` | Convertir telemetría persistida en dataset operable | Uno o varios artefactos de telemetría | Dataset, manifiesto y trazabilidad de preparación |
| `neural train mlp` | Entrenar un `MLP` individual | Dataset preparado | Checkpoint `MLP`, resumen legible y manifiesto de entrenamiento |
| `neural train gru` | Entrenar un `GRU` individual | Dataset preparado | Checkpoint `GRU`, resumen legible y manifiesto de entrenamiento |
| `neural train lstm` | Entrenar un `LSTM` individual | Dataset preparado | Checkpoint `LSTM`, resumen legible y manifiesto de entrenamiento |
| `neural train compare` | Entrenar `MLP`, `GRU` y `LSTM` sobre la misma base experimental | Dataset preparado | Tres checkpoints coordinados y un manifiesto compartido |
| `neural benchmark main` | Ejecutar la comparativa principal | Tres checkpoints válidos | Benchmark principal persistido |
| `neural benchmark ood` | Ejecutar la batería OOD separada | Tres checkpoints válidos | Benchmark OOD persistido |
| `neural report main` | Generar el reporte final de la comparativa principal | Benchmark principal | Tabla, selección, figuras y reporte narrativo |
| `neural report ood` | Generar el reporte de robustez OOD | Benchmark OOD | Tabla OOD y reporte de robustez |
| `neural inspect checkpoint` | Leer un checkpoint y mostrar sus metadatos | Un checkpoint válido | Resumen humano o JSON de auditoría |

### Argumentos Comunes

Estos argumentos deben comportarse igual en todos los subcomandos que los acepten:

- `--workspace DIR`: raíz de artefactos de la ejecución; por defecto apunta al árbol `artifacts/neural/`.
- `--run-id ID`: identificador de ejecución; si no se proporciona, la CLI lo genera.
- `--seed INT`: semilla principal del experimento.
- `--split-seed INT`: semilla del split; si no se indica, hereda `--seed`.
- `--feature-mode {raw_observation,observation_plus_tracking_errors}`: modo de features del dataset y del entrenamiento.
- `--output-dir DIR`: directorio destino del artefacto principal de la etapa.
- `--overwrite`: permite reutilizar una salida existente solo cuando la etapa lo haga explícito.
- `--format {text,json}`: formato de salida de inspección cuando aplique.

### Argumentos Específicos Por Etapa

#### Dataset

- `--telemetry PATH [PATH ...]`: uno o varios artefactos de telemetría persistida.
- `--source-label TEXT`: etiqueta opcional para campañas con varias fuentes.
- `--episode-id-policy {scenario,hash}`: política de nombre del episodio cuando se empaqueta más de una fuente.

#### Entrenamiento Individual

Parámetros comunes a todas las arquitecturas:

- `--epochs INT`
- `--batch-size INT`
- `--learning-rate FLOAT`
- `--weight-decay FLOAT`
- `--feature-mode MODE`
- `--split-seed INT`
- `--seed INT`
- `--output-dir DIR`

Parámetros específicos de `MLP`:

- `--window-size INT`
- `--stride INT`
- `--hidden-layers INT[,INT,...]`

Parámetros específicos de `GRU` y `LSTM`:

- `--window-size INT`
  - Si no se indica, toma el valor por defecto de la arquitectura.
- `--stride INT`
- `--hidden-size INT`
- `--num-layers INT`
- `--dropout FLOAT`

#### Entrenamiento Comparativo

El modo comparativo comparte dataset, semilla, split y salida base, y permite overrides por arquitectura con prefijos explícitos:

- `--mlp-hidden-layers INT[,INT,...]`
- `--mlp-window-size INT`
- `--gru-hidden-size INT`
- `--gru-num-layers INT`
- `--gru-dropout FLOAT`
- `--gru-window-size INT`
- `--lstm-hidden-size INT`
- `--lstm-num-layers INT`
- `--lstm-dropout FLOAT`
- `--lstm-window-size INT`

Si un override no tiene prefijo de arquitectura en modo comparativo, debe rechazarse para evitar ambigüedad.

#### Benchmark Principal Y OOD

- `--mlp-checkpoint PATH`
- `--gru-checkpoint PATH`
- `--lstm-checkpoint PATH`
- `--scenarios PATH` solo si se abre una extensión futura; en la fase 1 el benchmark principal y el OOD usan sus baterías canónicas.

#### Reporte

- `--benchmark PATH`: ruta al benchmark persistido.
- `--candidate-models mlp gru lstm`: lista de candidatos a incluir; por defecto se mantiene la terna completa.

#### Inspección

- `--checkpoint PATH`
- `--format {text,json}`

## Convencion De Artefactos Y Metadatos

La convención recomendada separa etapa, tipo de benchmark y ejecución.

```text
artifacts/
  neural/
    <run-id>/
      dataset/
      train/
      benchmark/
      report/
```

### Nombres Por Etapa

| Etapa | Directorio recomendado | Archivo canónico | Sidecars mínimos |
| --- | --- | --- | --- |
| Dataset | `artifacts/neural/<run-id>/dataset/` | `dataset.json` o `dataset.parquet` según el formato físico elegido | `manifest.json`, `dataset-summary.md` |
| Entrenamiento `MLP` | `artifacts/neural/<run-id>/train/mlp/` | `checkpoint.pt` | `checkpoint-summary.json`, `training-manifest.json` |
| Entrenamiento `GRU` | `artifacts/neural/<run-id>/train/gru/` | `checkpoint.pt` | `checkpoint-summary.json`, `training-manifest.json` |
| Entrenamiento `LSTM` | `artifacts/neural/<run-id>/train/lstm/` | `checkpoint.pt` | `checkpoint-summary.json`, `training-manifest.json` |
| Benchmark principal | `artifacts/neural/<run-id>/benchmark/main/` | `benchmark.json` | `manifest.json`, `benchmark-summary.md` |
| Benchmark OOD | `artifacts/neural/<run-id>/benchmark/ood/` | `ood-benchmark.json` | `manifest.json`, `ood-benchmark-summary.md` |
| Reporte principal | `artifacts/neural/<run-id>/report/main/` | `report.md` | `comparison_table.md`, `selection.json`, `figures/` |
| Reporte OOD | `artifacts/neural/<run-id>/report/ood/` | `ood_report.md` | `ood_comparison_table.md`, `figures/` |
| Inspección | `artifacts/neural/<run-id>/inspect/` | `checkpoint-inspection.json` o `checkpoint-inspection.md` | opcional |

### Reglas De Convención

- Cada etapa escribe un `manifest.json` con metadatos mínimos aunque el artefacto principal sea binario o derivado.
- Los sidecars legibles nunca sustituyen al artefacto canónico; solo lo acompañan.
- El benchmark principal usa nombres neutros como `benchmark.json` y `report.md`.
- El benchmark OOD usa prefijos `ood-` o `ood_` de forma consistente para evitar reuso accidental.
- El payload persistido también debe guardar `benchmark_kind` y `scenario_set_key` para que la distinción sobreviva aunque cambie el nombre de la carpeta.
- Los reportes deben conservar la frontera metodológica: el principal puede incluir selección; el OOD no.

### Metadatos Minimos Por Artefacto

Todos los manifiestos deben incluir, como mínimo:

- `schema_version`
- `stage`
- `run_id`
- `created_at`
- `command`
- `argv`
- `seed`
- `split_seed`
- `feature_mode`
- `input_paths`
- `output_path`
- `artifact_kind`

Metadatos adicionales por etapa:

- Dataset: `source_telemetry_paths`, `episode_count`, `split_ratios`, `dataset_contract_version`, `traceability_policy`.
- Entrenamiento: `architecture`, `window_size`, `stride`, `hidden_layers` o `hidden_size`/`num_layers`/`dropout`, `epochs`, `batch_size`, `learning_rate`, `weight_decay`, `train_window_count`, `validation_window_count`.
- Benchmark: `benchmark_kind`, `scenario_set_key`, `checkpoint_paths`, `control_observation_source`, `tracking_state_source`, `scenario_count`.
- Reporte: `benchmark_path`, `selection_path` cuando aplique, `figure_paths`, `candidate_models`.

### Metadatos De Trazabilidad Que Ya Existen En El Codigo

Esta convención encaja con los contratos actuales y no los contradice:

- el control sigue calculándose desde `observed_state`
- la evaluación del seguimiento sigue anclada en `true_state`
- el dataset conserva `scenario_name`, `scenario_seed`, `controller_kind`, `controller_source`, `trajectory_kind` y `disturbance_regime`
- los checkpoints de `MLP` y de recurrentes ya almacenan arquitectura, configuración efectiva, normalización, split y history de entrenamiento
- los benchmarks ya almacenan trazas y tiempos de inferencia para que el reporte se regenere sin volver a ejecutar el simulador

## Errores De Uso Que La CLI Debe Validar Pronto

La CLI debe rechazar antes de empezar cualquier trabajo costoso:

- arquitectura desconocida o incompatible con el subcomando
- `train compare` con overrides no prefijados por arquitectura
- ruta de dataset, telemetría o checkpoint inexistente
- checkpoint incompatible con la arquitectura esperada
- benchmark principal sin los tres checkpoints requeridos
- benchmark OOD invocado como si fuera selección principal
- dataset vacío o sin episodios válidos
- directorio de salida ya ocupado cuando no se haya pedido `--overwrite`

## Revisión Manual Realizada Para Esta Fase

Esta guía se redactó tras revisar manualmente:

- `src/simulador_multirotor/app.py`
- `src/simulador_multirotor/dataset/` y sus pruebas relacionadas
- `src/simulador_multirotor/control/` y sus pruebas relacionadas
- `src/simulador_multirotor/benchmark.py`
- `src/simulador_multirotor/reporting.py`
- `tests/test_dataset_phase2.py`
- `tests/test_mlp_phase3.py`
- `tests/test_recurrent_phase4.py`
- `tests/test_reporting_phase5.py`
- `tests/test_robustness_phase6.py`

La conclusión de esa revisión es que el repo ya tiene el núcleo funcional; la fase 1 solo necesita una capa documental y de exposición pública coherente.
