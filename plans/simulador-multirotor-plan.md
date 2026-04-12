# Plan: Simulador modular para control inteligente de dron multirotor

> Source PRD: [docs/PRD_simulador_multirotor.md](/C:/Users/chris/Documents/Universidad/TFG/docs/PRD_simulador_multirotor.md)

## Architectural decisions

Durable decisions that apply across all phases:

- **Core product boundary**: el alcance cubre la Fase 1 del TFG, centrada en un simulador modular en Python para experimentación reproducible, no en una réplica completa del firmware ni en integración con hardware real.
- **Simulation interface**: el núcleo físico expone un estado continuo del vehículo y acepta como mandos thrust colectivo y torques en ejes cuerpo.
- **Control architecture**: el sistema se articula alrededor de un controlador base en cascada, con lazo interno de estabilización y lazo externo de seguimiento, bajo una interfaz plug-and-play para permitir sustitución futura.
- **Trajectory contract**: toda trayectoria, nativa o externa, recibe tiempo de simulación y configuración parametrizada, y devuelve una referencia estructurada con posición, velocidad, yaw, validez temporal y aceleración opcional.
- **Scenario schema**: cada escenario se describe mediante bloques estables de vehículo, estado inicial, configuración temporal, trayectoria, perturbaciones/ruido, controlador, telemetría/exportación y metadatos.
- **Telemetry model**: cada ejecución registra como mínimo tiempo, estado, referencia, error de seguimiento, acción de control y eventos relevantes de saturación o perturbación.
- **Native trajectory set**: la primera versión debe soportar rectas, círculos, espirales, curvas paramétricas sencillas y Lissajous.
- **Aerodynamic scope**: el primer modelo aerodinámico será simple, parametrizable y centrado en arrastre parásito y un término simplificado de efectos inducidos con impacto en hover.
- **Validation strategy**: la validación será comparativa y experimental, priorizando tests de comportamiento, reproducibilidad y plausibilidad física básica.
- **Sim-to-real preparation**: los contratos de datos y telemetría deben quedar preparados para recalibración futura con LiteWing y para sustituir el lazo externo PID por un controlador inteligente.

---

## Phase 1: Núcleo mínimo ejecutable

**User stories**: 1, 3, 4, 9, 10, 12, 13, 28, 31, 40

### What to build

Construir el primer camino completo de simulación extremo a extremo: un escenario nominal con estado inicial configurable, dinámica rígida 6 DOF básica, actuadores simplificados, controlador en cascada mínimo y un runner capaz de ejecutar una simulación completa con una referencia sencilla.

### Acceptance criteria

- [ ] Existe un flujo único y repetible para lanzar una simulación completa desde una configuración mínima.
- [ ] El simulador acepta condiciones iniciales explícitas y produce una evolución temporal coherente del estado del vehículo.
- [ ] El controlador base consume observaciones del simulador y emite thrust colectivo y torques sin depender de detalles internos del núcleo.
- [ ] La dinámica y los actuadores quedan encapsulados detrás de interfaces que permitan pruebas aisladas.
- [ ] Hay pruebas de comportamiento para gravedad, integración básica, saturación y consistencia dimensional de estados y mandos.

---

## Phase 2: Escenarios configurables y reproducibles

**User stories**: 2, 12, 13, 21, 22, 37, 38, 39

### What to build

Introducir el esquema mínimo de escenario como contrato estable del producto, incluyendo definición del vehículo, configuración temporal, metadatos de experimento, semilla y validación de configuración para que cada ejecución pueda repetirse y auditarse.

### Acceptance criteria

- [ ] Todo experimento puede describirse mediante un escenario con bloques estables y valores por defecto razonables.
- [ ] Los escenarios validan entradas incompletas o inconsistentes con errores claros.
- [ ] Ejecutar dos veces el mismo escenario con la misma semilla produce resultados equivalentes dentro de la tolerancia esperada.
- [ ] Los metadatos del escenario quedan asociados a la ejecución para mantener trazabilidad.
- [ ] Hay pruebas que validan reproducibilidad, valores por defecto y manejo de configuraciones inválidas.

---

## Phase 3: Trayectorias nativas y contrato de referencias

**User stories**: 5, 6, 7, 11, 23, 24, 37, 38

### What to build

Incorporar el contrato común de trayectorias y entregar un conjunto de trayectorias nativas demoables que atraviese todas las capas del sistema: selección desde escenario, generación de referencia, consumo por el controlador y ejecución por el runner.

### Acceptance criteria

- [ ] El simulador soporta al menos rectas, círculos, espirales, curvas paramétricas sencillas y Lissajous como trayectorias nativas.
- [ ] Todas las trayectorias, nativas o externas, se adaptan al mismo contrato de entrada y salida.
- [ ] El runner puede ejecutar trayectorias nativas y referencias externas sin lógica especial ad hoc fuera del contrato.
- [ ] La referencia entregada incluye como mínimo posición, velocidad, yaw y validez temporal.
- [ ] Hay pruebas para continuidad temporal, validez geométrica y comportamiento cuando una trayectoria agota su horizonte.

---

## Phase 4: Telemetría, exportación y métricas

**User stories**: 14, 15, 16, 17, 25, 26, 35

### What to build

Completar el camino de observabilidad del simulador para registrar telemetría estructurada, exportarla en formatos reutilizables y calcular métricas de seguimiento que permitan comparar ejecuciones y generar datasets consistentes.

### Acceptance criteria

- [ ] Cada ejecución registra tiempo, estado, referencia, error de seguimiento, acciones de control y eventos relevantes.
- [ ] La telemetría puede exportarse al menos a `CSV`, `JSON` y `NumPy`.
- [ ] Las métricas de seguimiento permiten comparar de forma consistente varias ejecuciones bajo una misma batería de escenarios.
- [ ] La estructura de salida preserva metadatos suficientes para análisis posterior y generación de datasets.
- [ ] Hay pruebas para integridad de esquemas, formatos exportados y resultados correctos de métricas sobre series sintéticas.

---

## Phase 5: Aerodinámica simple y perturbaciones

**User stories**: 8, 29, 30, 34, 39

### What to build

Extender el núcleo físico con un primer nivel de realismo adicional, incorporando arrastre parásito, un término inducido simplificado relevante en hover, y perturbaciones configurables como viento y ruido, manteniendo la arquitectura parametrizable y desacoplada.

### Acceptance criteria

- [ ] El modelo puede activar o desactivar efectos aerodinámicos simples sin cambiar el contrato del simulador.
- [ ] El escenario puede configurar viento, ruido y parámetros aerodinámicos desde la misma estructura estable.
- [ ] El comportamiento nominal sin perturbaciones sigue disponible para validación base.
- [ ] El simulador respeta saturaciones y restricciones físicas básicas bajo perturbaciones razonables.
- [ ] Hay pruebas de plausibilidad física y de compatibilidad entre perturbaciones configuradas y telemetría registrada.

---

## Phase 6: Visualización y análisis post-procesado

**User stories**: 18, 19, 20, 26, 27

### What to build

Añadir un camino de post-procesado que consuma la telemetría generada por el simulador y produzca visualizaciones 2D/3D y artefactos de análisis útiles para inspección rápida, comparación de experimentos y soporte a la memoria del TFG.

### Acceptance criteria

- [ ] La visualización está desacoplada del bucle principal de simulación y opera sobre telemetría persistida.
- [ ] Existen salidas de análisis 2D y 3D suficientes para inspeccionar trayectorias, actitud y error de seguimiento.
- [ ] El flujo de análisis permite comparar varias ejecuciones sin modificar el núcleo del simulador.
- [ ] Los artefactos generados son reutilizables en documentación técnica o memoria.
- [ ] Hay pruebas ligeras para generación de artefactos y consumo correcto de telemetría.

---

## Phase 7: Preparación para sim-to-real y control inteligente

**User stories**: 5, 32, 33, 35, 36

### What to build

Consolidar los contratos y puntos de extensión del simulador para dejar preparado el reemplazo futuro del lazo externo PID por un controlador inteligente y facilitar una calibración posterior del modelo con datos del LiteWing.

### Acceptance criteria

- [ ] La interfaz de control permite sustituir el controlador externo sin rediseñar el runner ni la dinámica.
- [ ] La estructura de telemetría y los parámetros del vehículo son lo bastante estables como para soportar recalibración posterior con datos reales.
- [ ] Los formatos de dataset y los contratos de observación/acción son reutilizables en la siguiente fase de aprendizaje inteligente.
- [ ] La documentación deja explícitos los puntos de extensión y las simplificaciones asumidas para la transición sim-to-real.
- [ ] Existe una batería mínima de escenarios de referencia que pueda reutilizarse para comparar PID frente a futuros controladores inteligentes.
