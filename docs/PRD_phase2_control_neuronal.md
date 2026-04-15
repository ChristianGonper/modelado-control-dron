# PRD: Fase 2 - Control neuronal para seguimiento de trayectorias

## Problem Statement

El simulador ya dispone de una base sólida para ejecutar escenarios reproducibles con dinámica 6-DoF, controlador clásico en cascada, trayectorias nativas, perturbaciones de viento, telemetría estructurada y métricas de seguimiento. Sin embargo, todavía no existe una fase formal que convierta esa infraestructura en una plataforma de experimentación para control neuronal.

El problema real de esta fase no es solo "entrenar una red". El TFG necesita una forma rigurosa de:

- generar datasets reproducibles a partir del controlador clásico actual
- entrenar varias arquitecturas neuronales bajo un contrato de entrada y salida compatible con el simulador
- reinyectar esas políticas dentro del runner para ejecutar vuelos completos
- comparar su rendimiento frente al baseline clásico con criterios cuantitativos y cualitativos homogéneos

Sin esa fase, cualquier resultado de aprendizaje quedaría débilmente sustentado: no habría protocolo de comparación claro, ni interfaz estable para cargar modelos entrenados, ni garantías de que los resultados de entrenamiento se traduzcan en comportamiento de vuelo reproducible dentro del simulador.

## Solution

Se incorporará una fase de control neuronal centrada en imitation learning a partir del controlador clásico existente. La solución se apoyará en la frontera ya preparada por el contrato de controlador y en la telemetría persistida del simulador para construir un pipeline completo: generación de demostraciones, preparación de dataset, entrenamiento supervisado, adaptación de modelos entrenados al contrato del runner y evaluación comparativa extremo a extremo.

La primera iteración comparará tres familias de controladores neuronales:

- MLP como baseline simple sin memoria explícita
- LSTM como candidata principal para dependencias temporales
- GRU como alternativa más ligera con memoria recurrente

La salida de cada política deberá mantenerse compatible con el contrato actual de mando del simulador. Por tanto, la opción preferida es que la red produzca una intención de control de alto nivel equivalente a la del controlador clásico: thrust colectivo y torques en ejes cuerpo. El paso a comandos por rotor solo debe contemplarse si resulta imprescindible y como extensión posterior, porque cambiaría innecesariamente la frontera ya estabilizada por el código actual.

La evaluación se hará con vuelos completos en escenarios reproducibles, usando trayectorias no vistas en entrenamiento y perturbaciones comparables entre controladores. El entregable de esta fase no es solo un modelo entrenado, sino una batería experimental reproducible que justifique qué arquitectura merece continuar en la siguiente etapa del TFG.

## User Stories

1. Como autor del TFG, quiero generar demostraciones con el controlador clásico actual, para disponer de un dataset base coherente con el simulador.
2. Como autor del TFG, quiero reutilizar telemetría persistida como fuente de dataset, para desacoplar la generación de datos de la fase de entrenamiento.
3. Como investigador, quiero dividir train, validation y test por trayectorias completas, para evitar fugas temporales entre particiones.
4. Como investigador, quiero registrar observación, referencia y acción en cada muestra, para entrenar políticas supervisadas con contexto suficiente.
5. Como investigador, quiero entrenar una MLP, para disponer de un baseline neuronal simple y rápido.
6. Como investigador, quiero entrenar una LSTM, para evaluar si la memoria temporal mejora el seguimiento de trayectorias.
7. Como investigador, quiero entrenar una GRU, para comparar un compromiso razonable entre coste y capacidad temporal.
8. Como investigador, quiero definir una representación de entrada estable para todas las arquitecturas, para que la comparación sea justa.
9. Como investigador, quiero definir una representación de salida común alineada con el contrato del simulador, para poder enchufar cualquier política entrenada sin tocar el runner.
10. Como desarrollador, quiero encapsular el preprocesado del dataset en un módulo profundo y testeable, para evitar lógica dispersa entre scripts.
11. Como desarrollador, quiero encapsular la inferencia de modelos entrenados detrás del contrato de controlador, para que el simulador no dependa de detalles de PyTorch.
12. Como investigador, quiero mantener la misma batería de escenarios para baseline clásico y políticas neuronales, para que la comparación sea homogénea.
13. Como investigador, quiero evaluar trayectorias no vistas durante el entrenamiento, para medir generalización y no simple copia del experto.
14. Como investigador, quiero medir RMSE y MAE de seguimiento, para cuantificar precisión de trayectoria.
15. Como investigador, quiero medir error en actitud y yaw, para evaluar estabilidad además de posición.
16. Como investigador, quiero medir IAE e ISE, para capturar acumulación de error durante toda la ejecución.
17. Como investigador, quiero medir suavidad de control, para detectar políticas que sigan bien pero generen mandos poco realistas.
18. Como investigador, quiero medir tiempo medio de inferencia en CPU, para evaluar coste computacional del controlador.
19. Como investigador, quiero medir robustez bajo perturbaciones más severas o no vistas, para identificar sobreajuste al dataset.
20. Como investigador, quiero comparar estabilidad cualitativa del vuelo, para detectar oscilaciones, overshoot o settling pobre aunque algunas métricas puntuales sean buenas.
21. Como usuario del simulador, quiero cargar un controlador neuronal entrenado dentro del runner, para ejecutar vuelos completos sin scripts ad hoc.
22. Como usuario del simulador, quiero que los metadatos de la ejecución indiquen qué modelo se usó, para mantener trazabilidad experimental.
23. Como desarrollador, quiero un adaptador claro entre checkpoint entrenado e interfaz del simulador, para poder cambiar de arquitectura sin reescribir el punto de integración.
24. Como desarrollador, quiero separar dataset, entrenamiento e inferencia online en módulos distintos, para poder probarlos y evolucionarlos por separado.
25. Como investigador, quiero una tabla consolidada clásico vs MLP vs LSTM vs GRU, para justificar la elección final en la memoria.
26. Como investigador, quiero generar gráficas de trayectoria deseada vs real y evolución temporal del error, para apoyar el análisis cuantitativo con evidencia visual.
27. Como autor del TFG, quiero documentar las simplificaciones y límites del enfoque de imitation learning, para no sobredimensionar la validez de los resultados.
28. Como autor del TFG, quiero dejar explícito qué riesgos impiden afirmar sim-to-real directo, para mantener rigor metodológico.
29. Como desarrollador, quiero que el pipeline acepte nuevos escenarios o nuevas arquitecturas sin romper el contrato principal, para mantener escalabilidad razonable.
30. Como autor del TFG, quiero poder seleccionar el mejor controlador neuronal con un criterio claro y repetible, para decidir la siguiente fase sin ambigüedad.

## Implementation Decisions

- Esta fase se apoyará en la arquitectura ya existente del simulador y no redefinirá el runner, la dinámica ni el contrato principal de control.
- El contrato objetivo para las políticas neuronales será el mismo `VehicleCommand` ya consumido por dinámica y runner.
- La salida preferida de la red será una intención de control de alto nivel equivalente a la del baseline: thrust colectivo y torque en cuerpo.
- La opción de predecir señales por rotor queda fuera de la iteración principal, porque introduciría más acoplamiento con mezcla y actuadores sin aportar una comparación limpia en esta fase.
- El dataset de entrenamiento se construirá desde telemetría persistida exportada por el simulador, no desde hooks ad hoc incrustados en el runner.
- Cada muestra deberá incluir, como mínimo, observación del dron, referencia activa y acción aplicada por el controlador experto.
- La representación de entrada debe alinearse con lo que realmente ve el controlador en el simulador. Si la telemetría distingue entre `true_state` y `observed_state`, el dataset debe definir explícitamente cuál usa la política.
- La decisión operativa de esta fase será entrenar la política con `observed_state` y `TrajectoryReference`, porque esa es la interfaz real consumida por cualquier controlador a través de `VehicleObservation`.
- `true_state` no se usará como entrada de entrenamiento ni de inferencia de la política; quedará reservado para etiquetado físico, auditoría y métricas de seguimiento.
- Cuando no haya ruido de observación configurado, `observed_state` coincidirá numéricamente con `true_state`; aun así, el dataset seguirá etiquetando esa vista como observación para no romper la semántica cuando aparezca ruido después.
- La política deberá consumir la misma familia de variables tanto offline como online. No se permitirá entrenar con columnas derivadas de `true_state` si luego no están disponibles en el camino de inferencia real.
- La evaluación debe separar dos planos: el controlador decide usando `observed_state`, pero el rendimiento de seguimiento se mide contra `true_state` para no confundir error físico con ruido sensorial.
- Para MLP se usará una ventana temporal explícita apilada en la entrada.
- Para LSTM y GRU se usará una secuencia temporal con longitud configurable y padding o batching consistente.
- La separación train, validation y test se hará por episodios completos o familias de trayectoria, nunca por filas mezcladas del mismo episodio.
- El protocolo de generación de datos debe cubrir escenarios nominales y perturbados ya soportados por el simulador, especialmente viento base y ráfagas según el modelo actual.
- La idea de variar "niveles de batería" solo podrá entrar en esta fase si se implementa un modelo de degradación física o limitación de actuador explícito. El repositorio actual no expone ese modelo, así que no debe asumirse como capacidad ya existente.
- Si se desea capturar degradación equivalente a batería en esta fase, debe formularse como una nueva perturbación o cambio paramétrico controlado, no como una propiedad implícita del simulador.
- Los checkpoints entrenados deben guardarse con metadatos suficientes para reconstruir arquitectura, normalización, tamaño de ventana, variables de entrada y variables de salida.
- La normalización del dataset debe persistirse junto al modelo, porque inferencia y entrenamiento deben usar exactamente la misma transformación.
- La integración online del modelo entrenado se resolverá con un adaptador o controlador explícito cuyo trabajo sea: cargar checkpoint, normalizar entrada, ejecutar inferencia y devolver `VehicleCommand`.
- PyTorch será la librería de entrenamiento e inferencia.
- La inferencia deberá ejecutarse en CPU como caso base de evaluación, salvo que explícitamente se quiera estudiar otra cosa.
- La batería de evaluación usará escenarios reproducibles y seeds controladas para permitir comparación directa entre baseline clásico y políticas candidatas.
- La comparación oficial de esta fase no se basará solo en loss de entrenamiento, sino en vuelos completos dentro del simulador.
- Las métricas actuales del repositorio son una base útil, pero la fase necesita ampliación para cubrir MAE, IAE, ISE, correlación, quizá R² por eje y suavidad temporal del control.
- La comparación debe distinguir entre métricas ya soportadas por el código y métricas nuevas requeridas por el PRD, para evitar prometer resultados sin una implementación clara.
- El criterio de selección final del mejor modelo combinará precisión de seguimiento, suavidad de mando, robustez y coste de inferencia.
- Esta fase debe producir artefactos reproducibles: escenarios usados, exports de telemetría, checkpoints, configuración de entrenamiento y tablas comparativas.

### Major Modules

- Módulo de extracción de dataset: transforma telemetría persistida en ejemplos supervisados versionados y reproducibles.
- Módulo de esquema de features: define variables de entrada, salida, ventana temporal y normalización compartida entre dataset e inferencia.
- Módulo de entrenamiento: entrena MLP, LSTM y GRU con una configuración homogénea y guarda checkpoints auditables.
- Módulo de evaluación offline: calcula métricas de validación sobre dataset y resume curvas de entrenamiento.
- Módulo de controlador neuronal: adapta un checkpoint entrenado al contrato del simulador y produce `VehicleCommand`.
- Módulo de benchmark experimental: ejecuta la batería de escenarios con baseline y candidatos, recoge telemetría y consolida métricas.
- Módulo de reporte de resultados: genera tablas y figuras comparativas listas para análisis del TFG.

### Recommended Technical Clarifications

- La comparación principal debe ser contra el controlador clásico actual como experto y baseline de ejecución.
- El objetivo inicial debe ser behavioral cloning puro. DAgger, RL fine-tuning o MPC híbrido quedan como extensiones posteriores.
- El primer alcance debe centrarse en seguimiento de trayectorias, no en aprendizaje de todo el stack de navegación.
- La evaluación de robustez debe utilizar perturbaciones que el simulador ya pueda expresar con garantías reproducibles.
- El contrato del simulador ya permite sustituir controladores; conviene preservar esa frontera y evitar que el runner importe directamente PyTorch.

### Observability Policy

- La observabilidad oficial de la fase será la definida por `VehicleObservation`: la política ve `observed_state` y la referencia activa.
- La propiedad `.state` del controlador debe entenderse como alias de compatibilidad de `observed_state`, no como permiso implícito para usar verdad física.
- El dataset supervisado tendrá una convención explícita de columnas de entrada basadas en observación. Esa convención queda fijada en esta PRD y no debe variar entre entrenamiento e inferencia.
- `true_state` podrá conservarse en el dataset ampliado solo para análisis, depuración y métricas, pero no formará parte del tensor de entrada del modelo candidato.
- Si en una iteración futura se añade ruido de actitud, sesgos o sensores más ricos, la política seguirá entrenándose sobre la observación disponible en ese momento; no se reabrirá la puerta a usar verdad física como shortcut.
- Toda tabla o figura comparativa debe declarar explícitamente esta convención: "control computed from observed state, tracking evaluated on true state".

### Input Features And Representation

- La representación canónica de la observación usará variables continuas ya presentes en el contrato del simulador.
- La actitud observada se representará con cuaternión unitario `orientation_wxyz`, no con Euler, para evitar discontinuidades angulares y mantener coherencia con la dinámica y el controlador actual.
- El yaw de referencia se codificará como `sin(yaw_ref)` y `cos(yaw_ref)`, no como ángulo bruto, para evitar saltos artificiales en `+-pi`.
- La primera versión del modelo no utilizará variables derivadas de verdad física ni features "privilegiadas".
- El vector base por muestra quedará fijado así:
  - `observed_position_m`: `x`, `y`, `z`
  - `observed_linear_velocity_m_s`: `vx`, `vy`, `vz`
  - `observed_orientation_wxyz`: `qw`, `qx`, `qy`, `qz`
  - `observed_angular_velocity_rad_s`: `wx`, `wy`, `wz`
  - `reference_position_m`: `x_ref`, `y_ref`, `z_ref`
  - `reference_velocity_m_s`: `vx_ref`, `vy_ref`, `vz_ref`
  - `reference_acceleration_m_s2`: `ax_ref`, `ay_ref`, `az_ref` cuando exista; si la trayectoria no la define, se rellenará con ceros y se documentará esa convención
  - `reference_yaw_encoding`: `sin(yaw_ref)`, `cos(yaw_ref)`
- Con esta definición, el input base por instante tendrá 21 features.
- Además del vector base, el pipeline derivará una segunda vista normalizada con errores explícitos de seguimiento para facilitar aprendizaje y comparación entre modelos.
- Esa vista de error añadirá:
  - `position_error_m = reference_position_m - observed_position_m`
  - `velocity_error_m_s = reference_velocity_m_s - observed_linear_velocity_m_s`
  - `yaw_error_encoding = sin(yaw_ref - yaw_obs)`, `cos(yaw_ref - yaw_obs)`
- Para calcular `yaw_obs` se permitirá convertir el cuaternión observado a yaw solo dentro del pipeline de features; el cuaternión completo seguirá presente como representación primaria de actitud.
- La política candidata podrá entrenarse en uno de estos dos modos claramente etiquetados:
  - `raw_observation`: usa solo el vector base de 21 features
  - `observation_plus_tracking_errors`: usa el vector base más errores explícitos
- La recomendación inicial de esta PRD es usar `observation_plus_tracking_errors` como configuración principal, porque el baseline clásico ya opera conceptualmente sobre errores de posición, velocidad y actitud.
- La comparación entre arquitecturas debe mantener fijo el mismo modo de features para que la diferencia venga del modelo, no de la representación.
- Para MLP, la ventana temporal se formará concatenando el vector de features de varios instantes consecutivos.
- Para LSTM y GRU, cada paso temporal consumirá exactamente el mismo vector de features por instante, sin reordenamientos específicos por arquitectura.
- Todas las features continuas, salvo el cuaternión ya normalizado y las codificaciones seno/coseno, se estandarizarán con estadísticas calculadas solo sobre train.
- Los cuaterniones de entrada deberán re-normalizarse en preprocesado si aparece deriva numérica en exportación o carga.
- La salida objetivo de la red se mantendrá en el espacio de control actual:
  - `collective_thrust_newton`
  - `body_torque_nm_x`
  - `body_torque_nm_y`
  - `body_torque_nm_z`
- Por tanto, el target supervisado por instante tendrá 4 dimensiones.

### Temporal Windowing And Batching

- La frecuencia base del dataset quedará fijada en la cadencia real de control del escenario, no en una reinterpolación arbitraria posterior.
- Si un escenario usa `control_dt_s = 0.01`, las ventanas se interpretarán a 100 Hz. Si en el futuro aparece otra cadencia de control, el pipeline deberá documentarla y mantener la conversión a segundos de cada ventana.
- La generación de muestras se hará con sliding window sobre episodios completos y nunca cruzará el límite entre trayectorias.
- El stride por defecto para crear ventanas será de 10 pasos en train y validation.
- En test de evaluación principal se permitirá stride 1 para obtener curvas más densas, siempre sin mezclar episodios entre splits.
- La configuración inicial que queda fijada en esta PRD es:
  - `MLP`: ventana de 30 pasos, equivalente a 0.3 s cuando `control_dt_s = 0.01`
  - `GRU`: secuencia de 100 pasos, equivalente a 1.0 s cuando `control_dt_s = 0.01`
  - `LSTM`: secuencia de 150 pasos, equivalente a 1.5 s cuando `control_dt_s = 0.01`
- La justificación es separar un baseline denso de memoria corta de dos modelos recurrentes con contexto suficiente para capturar dinámica angular, retardos de actuador y correlación temporal de perturbaciones.
- Para MLP, cada muestra se construirá concatenando los vectores de features de los 30 instantes de la ventana en un único tensor 1D.
- Para GRU y LSTM, cada muestra se mantendrá como tensor temporal `[sequence_length, feature_dim]`.
- GRU y LSTM se entrenarán en modo stateless por secuencia; el estado oculto se reiniciará al inicio de cada secuencia del batch.
- No se usará entrenamiento stateful entre batches en la primera iteración, para evitar acoplar el pipeline a la continuidad exacta del loader y complicar la reproducibilidad.
- El batching de MLP podrá usar shuffle aleatorio estándar porque cada muestra ya encapsula su historia temporal.
- El batching de GRU y LSTM usará batches de secuencias contiguas del mismo tamaño o padded batches cuando haga falta; no se mezclarán timesteps aislados como si fueran IID.
- La longitud de ventana seguirá siendo un hiperparámetro registrable, pero la batería base de comparación arrancará con `30 / 100 / 150` para `MLP / GRU / LSTM`.
- Los valores candidatos autorizados para ajuste posterior quedan acotados inicialmente a `20`, `50`, `100` y `150` pasos.
- Si una arquitectura cambia de ventana durante tuning, esa variación deberá quedar reflejada en los metadatos del checkpoint y en las tablas comparativas.

### Train Validation Test Split Policy

- La partición oficial del dataset se hará por episodios completos, nunca por muestras individuales ni por ventanas mezcladas del mismo episodio.
- La unidad mínima de split será una ejecución completa del runner con un escenario, una seed y una trayectoria concretos.
- La ratio oficial del split principal será `70/15/15` para `train/validation/test`.
- La asignación deberá ser estratificada por buckets experimentales para conservar proporciones comparables entre tipos de trayectoria y niveles de perturbación.
- Un bucket experimental se definirá como combinación de:
  - familia de trayectoria
  - régimen de perturbación
  - nivel de agresividad cinemática cuando aplique
- Para esta fase, la recomendación mínima de familias de trayectoria será: `hover`, `line`, `circle`, `spiral`, `lissajous` y cualquier otra familia paramétrica ya disponible que se quiera añadir de forma explícita a la batería.
- Para esta fase, los regímenes de perturbación principales serán: nominal sin perturbaciones, viento base, viento con ráfagas, y ruido de observación cuando se active.
- `train` contendrá familias y perturbaciones vistas con diversidad amplia de parámetros y seeds.
- `validation` contendrá las mismas familias generales que train, pero con parámetros y seeds no vistos, para seleccionar hiperparámetros y aplicar early stopping sin leakage.
- `test` contendrá episodios completos no vistos de las mismas familias experimentales del split principal, con parámetros y seeds distintos de train y validation.
- La selección del mejor modelo se hará con `validation` y el informe principal de rendimiento se hará sobre `test`.
- Además del split principal, la fase incluirá una batería separada de robustez fuera de distribución.
- Esa batería de robustez no se usará para elegir hiperparámetros y no formará parte del `70/15/15`.
- La batería de robustez podrá incluir:
  - parámetros geométricos más extremos dentro de familias conocidas
  - perturbaciones más severas que las usadas en train
  - combinaciones de ruido y viento no vistas
  - cambios paramétricos del vehículo solo si se modelan explícitamente en el simulador
- Esta separación evita mezclar dos preguntas distintas:
  - generalización dentro de la distribución experimental prevista
  - robustez ante condiciones más duras o parcialmente fuera de distribución
- El split deberá ser determinista con una seed fija de partición para que los resultados sean repetibles.
- Toda ventana heredará el split del episodio del que proviene; no se permitirá que dos ventanas del mismo vuelo acaben en conjuntos distintos.

## Testing Decisions

- Una buena prueba debe validar comportamiento observable y contratos estables, no detalles internos del tensor layout o de la implementación concreta del modelo.
- El módulo de extracción de dataset debe probar que produce pares entrada/salida coherentes, tamaños esperados y particiones deterministas para una misma telemetría.
- El módulo de esquema de features debe probar orden, dimensionalidad, normalización y compatibilidad entre entrenamiento e inferencia.
- El módulo de checkpoints debe probar que un modelo guardado puede recargarse sin ambigüedad junto con su configuración y estadísticas de normalización.
- El controlador neuronal debe probar que transforma una observación y referencia válidas en un `VehicleCommand` válido sin depender del runner.
- El benchmark experimental debe probar que baseline y candidatos se ejecutan sobre escenarios homogéneos y que la consolidación de resultados conserva trazabilidad por controlador y escenario.
- Las pruebas deben cubrir tanto modelos sin memoria explícita como modelos recurrentes, especialmente manejo de estado inicial, reset entre episodios y longitud de secuencia.
- La evaluación de métricas debe probar resultados correctos en series sintéticas pequeñas donde RMSE, MAE, IAE e ISE puedan verificarse manualmente.
- Las pruebas deben comprobar que la selección por episodios evita mezclar ventanas del mismo vuelo entre train y test.
- Deben existir tests de integración cortos que demuestren que un checkpoint entrenado o un stub equivalente puede enchufarse al runner mediante el contrato de controlador.
- El patrón de prior art dentro del repositorio ya existe en tests de contratos, runner, aerodinámica, escenarios y métricas; conviene seguir ese estilo de pruebas deterministas, pequeñas y con invariantes claros.
- Los módulos prioritarios para test intensivo son: extracción de dataset, esquema de features, adaptador de controlador neuronal, ampliación de métricas y benchmark de comparación.
- Las pruebas de entrenamiento completo deben mantenerse acotadas y rápidas; para CI o regresión conviene usar datasets mínimos o modelos pequeños.

## Out of Scope

- Reinforcement learning, DAgger o fine-tuning online del controlador.
- Predicción directa a nivel de rotor como camino principal de esta fase.
- Validación sim-to-real sobre el dron físico.
- Conclusiones de alto nivel sobre robustez frente a fenómenos físicos que el simulador todavía no modela.
- Modelado detallado de batería si antes no se implementa una perturbación o restricción explícita para ello.
- Búsqueda masiva de hiperparámetros o AutoML.
- Integración en tiempo real o despliegue embebido.
- Añadir nuevas familias complejas de modelos como Transformers o TCN en la iteración principal.

## Further Notes

- La idea original está bien orientada, pero conviene fijar una decisión fuerte de alcance: en esta fase se aprende a imitar el controlador clásico y se compara dentro del simulador, no se resuelve todavía el salto a hardware.
- Hay una oportunidad clara de reutilizar decisiones ya asentadas en el repositorio, especialmente el contrato de controlador reemplazable y la recomendación explícita de construir datasets a partir de telemetría persistida.
- El mayor riesgo metodológico es entrenar sobre una representación de estado demasiado cercana al experto y luego evaluar sin dejar claro qué observabilidad real usa la política. Esa decisión debe documentarse desde el principio.
- En esta PRD esa decisión queda cerrada así: entrenamiento e inferencia usan observación; evaluación usa estado físico verdadero.
- El segundo riesgo fuerte es medir éxito solo con loss de entrenamiento. El PRD lo evita al exigir vuelos completos y comparación homogénea contra el baseline clásico.
- Si más adelante quieres introducir degradación tipo batería, mi recomendación es tratarla como un slice posterior bien definido, porque ahora mismo sería una mezcla de hipótesis física y objetivo experimental sin soporte directo en el código actual.
