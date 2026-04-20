# Main Interfaces and Classes

## Purpose

Esta ficha resume las abstracciones principales con valor explicativo para el
TFG. No replica docstrings ni lista todos los metodos; se centra en rol,
colaboradores, invariantes y lugar dentro de la arquitectura.

Modulos relacionados:

- [Execution, Scenarios, and Core Contracts](/Users/chris/Documents/Universidad/TFG/docs/software/execution-scenarios-and-core-contracts.md)
- [Control, Trajectories, and Dynamics](/Users/chris/Documents/Universidad/TFG/docs/software/control-trajectories-and-dynamics.md)
- [Telemetry, Dataset, and Experimental Outputs](/Users/chris/Documents/Universidad/TFG/docs/software/telemetry-dataset-and-experimental-outputs.md)

## `SimulationScenario`

- Kind: concrete class
- Code location: `src/simulador_multirotor/scenarios/schema.py`
- Role:
  contrato agregador de una ejecucion reproducible; concentra configuracion,
  fabrica de dependencias y serializacion versionada
- Main collaborators:
  `SimulationRunner`, `RigidBody6DOFDynamics`, `TrajectoryContract`,
  `ControllerContract`
- Contract or behavior:
  expone `build_rng()`, `build_dynamics()`, `build_controller()`,
  `build_trajectory()`, `to_dict()`, `from_dict()` y `describe()`
- Invariants and constraints:
  `initial_state` y subconfiguraciones tipadas; `control_dt_s` y
  `telemetry_dt_s` deben ser multiplos enteros de `physics_dt_s`
- Extension and replacement notes:
  admite nuevas familias de trayectorias, perturbaciones o controladores
  mientras mantengan las superficies ya fijadas
- Traceability:
  parent module `scenarios/schema.py`; system block configuracion experimental;
  ADR-003 y ADR-010

## `SimulationRunner`

- Kind: concrete class
- Code location: `src/simulador_multirotor/runner.py`
- Role:
  orquestador del flujo principal; coordina tiempos, observacion, control y
  muestreo sin apropiarse de la logica de cada subsistema
- Main collaborators:
  `SimulationScenario`, `ControllerContract`, `TrajectoryContract`,
  `RigidBody6DOFDynamics`, `SimulationHistory`
- Contract or behavior:
  `run(scenario, controller=None) -> SimulationHistory`
- Invariants and constraints:
  registra muestras sincronizadas; conserva eventos y metadatos suficientes para
  trazabilidad experimental
- Extension and replacement notes:
  puede aceptar un controlador inyectado, pero sigue dependiendo del contrato
  oficial de observacion, referencia y comando
- Traceability:
  parent module `runner.py`; system block orquestacion; ADR-002, ADR-009,
  ADR-010

## `VehicleState`

- Kind: concrete class
- Code location: `src/simulador_multirotor/core/contracts.py`
- Role:
  estado canonico del vehiculo en el sistema modelado
- Main collaborators:
  `VehicleObservation`, `SimulationStep`, `RigidBody6DOFDynamics`
- Contract or behavior:
  contiene posicion, orientacion quaternion, velocidades lineales y angulares,
  y `time_s`
- Invariants and constraints:
  vectores con dimensiones fijas; quaternion unitario; tiempo finito
- Extension and replacement notes:
  cualquier extension debe seguir siendo un valor inmutable compartible entre
  dinamica, control y telemetria
- Traceability:
  parent module `core/contracts.py`; system block contratos compartidos;
  ADR-001

## `VehicleObservation`

- Kind: concrete class
- Code location: `src/simulador_multirotor/core/contracts.py`
- Role:
  separar lo que ocurre en la planta de lo que observa el controlador
- Main collaborators:
  `SimulationRunner`, `ControllerContract`, `DatasetSample`
- Contract or behavior:
  agrupa `true_state`, `observed_state` y metadatos; mantiene alias `.state`
  para compatibilidad
- Invariants and constraints:
  `true_state` y `observed_state` deben referirse al mismo instante
- Extension and replacement notes:
  pueden anadirse metadatos, pero no debe perderse la distincion entre verdad de
  planta y observacion disponible
- Traceability:
  parent module `core/contracts.py`; system block contratos compartidos;
  ADR-009 y ADR-011

## `TrajectoryReference`

- Kind: concrete class
- Code location: `src/simulador_multirotor/core/contracts.py`
- Role:
  muestra temporal comun que une trayectorias y control
- Main collaborators:
  `TrajectoryContract`, `ControllerContract`, `TrackingError`
- Contract or behavior:
  expresa posicion, velocidad, yaw, aceleracion opcional y ventana de validez
- Invariants and constraints:
  `time_s` dentro de `[valid_from_s, valid_until_s]` cuando hay horizonte
- Extension and replacement notes:
  puede enriquecerse con metadatos, pero la referencia temporal comun debe
  seguir siendo interpretable por runner, control y dataset
- Traceability:
  parent module `core/contracts.py`; system block interfaces principales;
  ADR-004

## `VehicleCommand`

- Kind: concrete class
- Code location: `src/simulador_multirotor/core/contracts.py`
- Role:
  representar la accion de control sin acoplar obligatoriamente la interfaz a
  senales por rotor
- Main collaborators:
  `ControllerContract`, `RotorMixer`, `RigidBody6DOFDynamics`
- Contract or behavior:
  encapsula `VehicleIntent`, comandos por rotor opcionales y metadatos
- Invariants and constraints:
  no admite nombres de rotor duplicados; el intento y los accesos derivados deben
  ser coherentes
- Extension and replacement notes:
  permite evolucionar mezcla y actuacion sin cambiar la frontera del
  controlador
- Traceability:
  parent module `core/contracts.py`; system block control; ADR-008 y ADR-010

## `TrajectoryContract`

- Kind: interface
- Code location: `src/simulador_multirotor/trajectories/contract.py`
- Role:
  interfaz minima para cualquier generador de referencias
- Main collaborators:
  `SimulationScenario`, `SimulationRunner`, `ControllerContract`
- Contract or behavior:
  `reference_at(time_s) -> TrajectoryReference`,
  `is_complete_at(time_s) -> bool`
- Invariants and constraints:
  expone `kind`, `source`, `duration_s` y `parameters`
- Extension and replacement notes:
  una nueva trayectoria solo debe implementar esta superficie y mantener la
  semantica temporal de `TrajectoryReference`
- Traceability:
  parent module `trajectories/contract.py`; system block trayectorias; ADR-004

## `ControllerContract`

- Kind: interface
- Code location: `src/simulador_multirotor/control/contract.py`
- Role:
  interfaz comun para baseline clasico y controladores neuronales
- Main collaborators:
  `SimulationRunner`, `VehicleObservation`, `TrajectoryReference`
- Contract or behavior:
  `compute_action(observation, reference) -> VehicleCommand`
- Invariants and constraints:
  expone `kind`, `source` y `parameters`; debe devolver siempre un
  `VehicleCommand` valido
- Extension and replacement notes:
  es la principal frontera de reemplazo del simulador
- Traceability:
  parent module `control/contract.py`; system block control reemplazable;
  ADR-008, ADR-009 y ADR-015

## `SimulationHistory`

- Kind: concrete class
- Code location: `src/simulador_multirotor/telemetry/memory.py`
- Role:
  contenedor estable de la historia completa de una ejecucion
- Main collaborators:
  `SimulationRunner`, exportadores de telemetria, metricas, dataset
- Contract or behavior:
  conserva `initial_state`, `steps` y metadatos de escenario, vehiculo,
  controlador y telemetria
- Invariants and constraints:
  las muestras deben ser temporalmente coherentes y aptas para persistencia y
  reapertura
- Extension and replacement notes:
  puede ampliarse con metadatos, pero debe seguir siendo la base comun para
  exportacion, metricas y dataset
- Traceability:
  parent module `telemetry/memory.py`; system block telemetria;
  ADR-005 y ADR-011

## `DatasetContract`

- Kind: concrete class
- Code location: `src/simulador_multirotor/dataset/contract.py`
- Role:
  fijar el vocabulario oficial de features y targets para aprendizaje
- Main collaborators:
  `DatasetEpisode`, `DatasetWindow`, `MLPController`, `RecurrentController`
- Contract or behavior:
  define `feature_modes`, nombres de features, nombres de targets y dimensiones
  derivadas
- Invariants and constraints:
  el contrato debe permanecer estable para permitir entrenamiento,
  benchmarking e inferencia comparables
- Extension and replacement notes:
  cualquier cambio exige revisar compatibilidad con checkpoints, windowing y
  reporting
- Traceability:
  parent module `dataset/contract.py`; system block dataset para aprendizaje;
  ADR-013 y ADR-014

## `DatasetEpisode`

- Kind: concrete class
- Code location: `src/simulador_multirotor/dataset/contract.py`
- Role:
  unidad de trazabilidad experimental reutilizable para aprendizaje
- Main collaborators:
  `DatasetSample`, `DatasetTraceability`, `DatasetSplitContext`,
  `DatasetWindow`
- Contract or behavior:
  agrupa muestras, metadatos, estado inicial/final y acceso a matrices de
  features y targets
- Invariants and constraints:
  `episode_id` no vacio; las muestras deben ser instancias validas del contrato
  oficial
- Extension and replacement notes:
  puede enriquecerse con contexto de split o procedencia, pero sin romper la
  capacidad de reapertura desde telemetria persistida
- Traceability:
  parent module `dataset/contract.py`; system block dataset;
  ADR-013 y ADR-014

## Notes

- La seleccion se centra en abstracciones que permiten explicar observacion,
  estado, comando, referencia y ejecucion.
- Clases como `CascadedController`, `RigidBody6DOFDynamics`, `TrackingError` o
  `DatasetWindow` quedan tratadas como colaboradores estructurales dentro de las
  fichas modulares, no como fichas individuales, para evitar
  sobredocumentacion.
