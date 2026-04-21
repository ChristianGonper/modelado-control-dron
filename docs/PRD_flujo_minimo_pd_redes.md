# PRD: Flujo Mínimo Repetible Desde PD Hasta Redes

## Problem Statement

El simulador ya dispone de dinámica 6DOF, trayectorias nativas, configuración de escenarios, telemetría persistida, preparación de dataset, entrenamiento supervisado de `MLP`/`GRU`/`LSTM`, benchmark y reporting. Sin embargo, esas piezas aún no están cerradas como un flujo mínimo único que parta de un dron genérico bien parametrizado, pase por un controlador PD correctamente ajustado para seguir una trayectoria útil y termine en un pipeline de entrenamiento y evaluación que pueda repetirse variando parámetros sin rehacer el trabajo conceptual.

Para el TFG, el problema no es solo "tener módulos", sino poder demostrar una cadena experimental completa y trazable:

- definir un dron genérico con parámetros físicos y de control explícitos
- documentar qué significa cada parámetro y qué rango operativo tiene
- lograr una referencia inicial que el PD siga de forma estable y defendible
- usar esa ejecución como baseline experto para generar telemetría reutilizable
- convertir esa telemetría en dataset reproducible para redes
- entrenar y evaluar las redes con un contrato homogéneo
- dejar una guía suficientemente clara como para repetir el proceso cambiando masas, inercias, ganancias, tiempos o trayectorias

Hoy esa historia completa todavía no está fijada como artefacto metodológico principal del repositorio. La consecuencia es fricción para repetir experimentos, ambigüedad sobre qué configuración constituye el baseline correcto y riesgo de que parte del valor del TFG quede implícito en conocimiento no documentado.

## Solution

Se definirá un flujo mínimo repetible, de extremo a extremo, cuyo primer objetivo será establecer una baseline física y de control defendible antes de entrenar redes. La solución fijará una línea base experimental única:

1. un dron genérico de referencia con parámetros físicos, de actuadores y de control documentados
2. un escenario mínimo de validación PD que demuestre estabilidad y seguimiento aceptable
3. una batería pequeña y explícita de trayectorias para generar telemetría experta útil para entrenamiento
4. un pipeline operable para preparar dataset, entrenar redes, ejecutar benchmark y generar reporte final
5. una documentación de uso y trazabilidad que permita repetir el flujo modificando parámetros sin cambiar el contrato general

La idea no es añadir complejidad innecesaria ni perseguir fidelidad hardware-específica en esta iteración. El foco será dejar un vertical slice sólido y repetible para el TFG:

- el PD debe funcionar correctamente sobre un dron genérico parametrizado
- la configuración de referencia debe quedar congelada y explicada
- las redes deben entrenarse sobre telemetría generada desde esa baseline
- el cierre experimental debe producir artefactos y documentación listos para reejecución y comparación

## User Stories

1. Como autor del TFG, quiero un dron genérico de referencia con parámetros físicos explícitos, para no depender de supuestos implícitos del código.
2. Como autor del TFG, quiero que los parámetros del dron estén documentados con significado, unidades y rol dentro del simulador, para poder justificarlos en la memoria.
3. Como usuario, quiero saber qué parámetros son físicos, cuáles son del controlador y cuáles son del experimento, para no mezclar capas conceptuales.
4. Como investigador, quiero una configuración baseline congelada del dron genérico, para poder repetir resultados sin reinterpretar el setup.
5. Como investigador, quiero que el baseline no dependa de un dron comercial o de un hardware exacto, para mantener el proyecto en el nivel de abstracción correcto.
6. Como usuario, quiero un escenario mínimo con trayectoria claramente definida, para validar rápido si el PD está funcionando.
7. Como usuario, quiero criterios de aceptación explícitos para la trayectoria PD, para saber cuándo la baseline es suficientemente buena para generar dataset.
8. Como autor del TFG, quiero distinguir entre escenario de validación PD y escenarios de generación de dataset, para no confundir objetivos.
9. Como investigador, quiero una trayectoria mínima estable de hover y una maniobra sencilla adicional de traslación o seguimiento, para que el experto produzca datos útiles y no triviales.
10. Como usuario, quiero que las ganancias PD queden asociadas al dron baseline y no dispersas en varios documentos, para poder ajustarlas con criterio.
11. Como usuario, quiero poder modificar masa, inercia, límites de empuje y ganancias desde el contrato de escenario, para repetir el flujo con variantes controladas.
12. Como usuario, quiero saber qué combinaciones de parámetros son inválidas o arriesgadas, para fallar pronto y no obtener resultados engañosos.
13. Como usuario, quiero ejecutar la simulación baseline y exportar telemetría con un comando claro, para generar el punto de partida del pipeline.
14. Como usuario, quiero que la telemetría baseline conserve suficiente metadata de escenario, controlador y referencia, para soportar trazabilidad experimental.
15. Como investigador, quiero una batería mínima de trayectorias nativas para generación de dataset, para entrenar redes con señal diversa pero todavía controlable.
16. Como investigador, quiero que esa batería mínima quede documentada como parte del protocolo experimental, para no cambiarla accidentalmente entre corridas.
17. Como usuario, quiero preparar el dataset desde telemetría persistida sin scripts ad hoc, para mantener el flujo repetible.
18. Como investigador, quiero que la configuración del dataset registre seeds, feature mode, split y procedencia de episodios, para garantizar reproducibilidad.
19. Como usuario, quiero entrenar `MLP`, `GRU` y `LSTM` con el mismo contrato experimental, para comparar arquitecturas sin sesgos operativos.
20. Como usuario, quiero inspeccionar checkpoints y configuraciones efectivas, para reconstruir qué parámetros generaron cada resultado.
21. Como investigador, quiero separar claramente baseline experto, dataset, entrenamiento, benchmark principal y robustez OOD, para mantener coherencia metodológica.
22. Como autor del TFG, quiero un benchmark final frente al PD baseline, para evaluar si las redes reproducen o superan el comportamiento experto bajo el criterio fijado.
23. Como autor del TFG, quiero un reporte final con tablas, selección y figuras, para reutilizar directamente los resultados en la memoria.
24. Como usuario, quiero una guía paso a paso del flujo mínimo, para poder rerunear todo cambiando solo algunos parámetros.
25. Como usuario, quiero una tabla o convención de parámetros modificables, para saber qué tocar cuando quiera repetir el experimento con otra masa, otra trayectoria o distintas ganancias.
26. Como desarrollador, quiero preservar los contratos existentes de escenario, controlador, dataset y benchmark, para aprovechar la arquitectura ya construida.
27. Como desarrollador, quiero evitar lógica duplicada entre el flujo mínimo PD y el flujo neuronal, para no crear dos caminos incompatibles.
28. Como revisor académico, quiero ver claramente qué supuestos simplifican la física y cuáles limitan la validez externa, para interpretar correctamente los resultados.
29. Como revisor académico, quiero que la frontera entre observación usada por la política y estado verdadero usado para evaluación quede documentada, para evitar ambigüedad metodológica.
30. Como autor del TFG, quiero que la repetición del flujo dependa de parámetros declarados y artefactos persistidos, no de memoria operativa del desarrollador.

## Implementation Decisions

- Se fijará un único perfil de vehículo baseline denominado conceptualmente "dron genérico de referencia", modelado como cuadricóptero `X` con parámetros físicos y de actuadores explícitos.
- Ese perfil baseline será abstracto y defendible, no una réplica de hardware real. Podrá inspirarse en órdenes de magnitud realistas, pero se documentará como vehículo genérico de simulación.
- Los parámetros del dron baseline se agruparán por categorías:
  - masa y gravedad
  - inercias principales
  - límites de empuje y par
  - constante temporal de motor
  - geometría de rotores y signos de giro
  - parámetros aerodinámicos agregados
- La documentación del baseline deberá explicar para cada parámetro:
  - unidad
  - efecto esperado sobre la simulación
  - dependencia o acoplamiento principal
  - criterio de modificación recomendado
- El flujo mínimo distinguirá tres niveles de escenarios:
  - escenario de validación PD
  - batería mínima de generación de dataset
  - escenarios de benchmark final y OOD
- El escenario de validación PD será deliberadamente simple y deberá validar al menos estabilidad en hover y seguimiento razonable de una referencia cinemáticamente simple.
- La generación de dataset no dependerá de una única trayectoria trivial; usará una batería mínima pequeña, explícita y repetible basada en trayectorias nativas ya soportadas.
- La baseline experta seguirá siendo el controlador en cascada actual de tipo PD/PD-like, con parámetros asociados al vehículo baseline y persistidos como parte de la metadata experimental.
- Antes del entrenamiento neuronal se incorporará una etapa formal de validación del experto con criterios observables de aceptación, por ejemplo:
  - error RMS de posición acotado
  - ausencia de saturación persistente
  - estabilidad sin divergencia ni oscilación sostenida
  - consistencia temporal de tiempos `physics/control/telemetry`
- Solo una baseline PD que cumpla esos criterios podrá considerarse fuente válida para dataset de entrenamiento.
- La trazabilidad experimental deberá mantener el vínculo entre:
  - perfil de dron
  - trayectoria o batería usada
  - ganancias del controlador
  - semillas
  - artefactos de telemetría, dataset, checkpoint, benchmark y reporte
- El flujo operable reutilizará la CLI neuronal ya existente y añadirá o consolidará la parte anterior del pipeline:
  - selección del baseline de vehículo
  - validación de trayectoria PD
  - exportación de telemetría experta
  - generación de batería mínima de episodios
- La preparación de dataset seguirá usando telemetría persistida como fuente única; no se añadirá una vía paralela desde hooks internos del runner.
- La documentación final deberá incluir dos recorridos:
  - recorrido mínimo: validar baseline PD y generar un primer dataset entrenable
  - recorrido completo: entrenar `MLP`, `GRU`, `LSTM`, benchmark principal, benchmark OOD y reporte final
- Los artefactos deberán seguir una convención estable que permita localizar con claridad:
  - configuración baseline del dron
  - escenarios utilizados
  - telemetrías fuente
  - dataset preparado
  - checkpoints
  - benchmarks
  - reporte final
- Se documentará explícitamente qué parámetros se pueden variar sin romper el contrato general del flujo:
  - parámetros físicos del vehículo
  - ganancias del PD
  - tiempos de simulación
  - trayectoria o batería mínima
  - feature mode y semillas
  - hiperparámetros de entrenamiento
- Se documentará también qué cambios invalidan comparaciones directas y obligan a tratarlos como una nueva campaña experimental.

### Major Modules

- Módulo de perfil de vehículo baseline: encapsula el dron genérico de referencia y sus parámetros documentados.
- Módulo de validación PD: ejecuta el escenario mínimo y decide si la baseline es apta para producir dataset.
- Módulo de batería mínima de trayectorias: define el conjunto pequeño y repetible de referencias para generar telemetría experta.
- Módulo de exportación de baseline experto: genera telemetría persistida con metadata suficiente para dataset y auditoría.
- Módulo de dataset operable: transforma telemetría persistida en dataset reproducible con trazabilidad.
- Módulo de entrenamiento neuronal: entrena `MLP`, `GRU` y `LSTM` sobre el mismo contrato experimental.
- Módulo de benchmark y reporting: compara PD y redes, separa benchmark principal y OOD, y genera la salida final.
- Módulo de documentación operativa: reúne guía, parámetros, criterios de aceptación y protocolo de repetición.

## Testing Decisions

- Una buena prueba debe validar comportamiento externo observable y reproducibilidad, no detalles accidentales de implementación.
- El perfil baseline del dron debe probarse para garantizar consistencia física mínima:
  - masa positiva
  - inercias positivas
  - empuje máximo suficiente para sostener el peso
  - cobertura coherente entre límites globales y rotores
- La validación PD debe probarse con escenarios deterministas y umbrales observables de seguimiento.
- Las pruebas del escenario baseline deben comprobar que la trayectoria mínima cumple los criterios de aceptación establecidos para el experto.
- Deben existir pruebas para fallar con mensajes claros cuando una configuración baseline sea físicamente incoherente o metodológicamente incompleta.
- La batería mínima de trayectorias debe probarse para asegurar que produce episodios persistibles y reutilizables por el pipeline de dataset.
- El flujo `baseline -> telemetría -> dataset -> entrenamiento -> benchmark -> reporte` debe cubrirse al menos con un smoke test determinista y pequeño.
- Las pruebas de CLI deben verificar que el usuario puede repetir el flujo sin scripts externos y que los artefactos quedan enlazados por manifests y metadatos.
- Las pruebas deben comprobar que cambiar un parámetro relevante queda reflejado en los artefactos persistidos, para soportar trazabilidad.
- Las pruebas deben preservar la separación metodológica entre benchmark principal y OOD.
- Los módulos prioritarios para test son:
  - perfil baseline del dron
  - validación PD
  - preparación reproducible de episodios fuente
  - encadenamiento dataset -> train -> benchmark -> report
  - documentación o manifests suficientes para reconstrucción experimental

## Out of Scope

- Ajustar el simulador para reproducir con alta fidelidad un dron comercial o un hardware concreto.
- Introducir control adaptativo, MPC, reinforcement learning o entrenamiento online.
- Hacer una búsqueda extensa de hiperparámetros de redes o de ganancias.
- Resolver identificación física frente a datos reales.
- Añadir interfaces gráficas interactivas o herramientas de tuning visual en tiempo real.
- Reestructurar toda la arquitectura del simulador más allá de lo necesario para consolidar este flujo mínimo.
- Convertir la baseline genérica en un modelo certificado para validación externa.

## Further Notes

- Este PRD reorganiza el proyecto alrededor de un vertical slice experimental claro: primero baseline física y PD, luego aprendizaje y evaluación.
- La principal carencia actual no es de capacidad técnica aislada, sino de cierre metodológico de la cadena completa.
- La baseline PD no debe verse como competidor final de alto rendimiento, sino como experto reproducible y bien documentado para generar datos y servir de referencia.
- La calidad de la documentación es parte del entregable técnico, no un añadido posterior: sin ella, el flujo no es realmente repetible.
- La solución debe mantener simplicidad operativa. Si el flujo mínimo requiere demasiadas decisiones implícitas, no cumple el objetivo del TFG.
- Supuesto de trabajo para esta iteración:
  - el vehículo seguirá siendo genérico
  - la primera validación PD priorizará estabilidad y seguimiento razonable sobre agresividad
  - el entrenamiento neuronal seguirá siendo imitation learning sobre telemetría experta generada en simulación
