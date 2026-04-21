# PRD: Flujo Operable De Control Neuronal

## Problem Statement

El simulador ya dispone de capacidades reales para el control neuronal: extracción de dataset desde telemetría persistida, entrenamiento supervisado para `MLP`, `GRU` y `LSTM`, carga de checkpoints en el runner, benchmark comparativo y generación de reportes. Sin embargo, esas capacidades siguen expuestas sobre todo como piezas de librería para desarrollador y como documentación repartida entre varias fases.

El problema para el usuario del TFG ya no es "si se puede entrenar una red", sino "cómo trabajar de forma clara, consistente y reproducible con las tres arquitecturas". Hoy no existe una experiencia única que permita:

- entender qué parámetros gobiernan cada arquitectura y cuáles son comunes
- lanzar el flujo completo desde CLI sin tener que montar scripts ad hoc
- saber qué artefactos se generan en cada etapa
- comparar las tres arquitecturas con un criterio homogéneo
- abrir y leer resultados sin depender del conocimiento interno del código
- documentar el uso operativo del control neuronal de forma apta para memoria, revisión académica y repetición experimental

Sin esa capa de operación clara, el proyecto tiene capacidad técnica pero no una forma suficientemente limpia de uso. Eso introduce fricción metodológica, dificulta repetir experimentos y debilita la trazabilidad de resultados dentro del TFG.

## Solution

Se incorporará una capa operable de control neuronal que convierta el pipeline ya existente en un flujo único, explícito y documentado para `MLP`, `GRU` y `LSTM`. La solución no reemplaza la arquitectura interna actual; la hace utilizable de extremo a extremo por CLI y deja fijado cómo deben entenderse parámetros, checkpoints, benchmarks y reportes.

La experiencia objetivo será:

1. preparar o reutilizar telemetría de demostración
2. construir dataset supervisado reproducible
3. entrenar una arquitectura concreta o las tres arquitecturas bajo un contrato homogéneo
4. inspeccionar parámetros efectivos y metadatos del checkpoint generado
5. ejecutar benchmark homogéneo frente al controlador clásico
6. generar reportes y figuras comparativas
7. leer un resumen final que indique qué arquitectura rindió mejor y por qué

La solución debe unificar tres capas que hoy están separadas:

- una CLI pública para el flujo neuronal completo
- una convención documental única para explicar parámetros, entradas, salidas y artefactos
- una convención de resultados para que cada ejecución deje evidencia reutilizable y comparable

El resultado buscado es que cualquier lector técnico del TFG pueda ejecutar, repetir y entender el flujo experimental de control neuronal sin tener que deducir el pipeline desde módulos internos.

## User Stories

1. Como autor del TFG, quiero un flujo único para control neuronal, para no depender de scripts temporales o conocimiento implícito.
2. Como autor del TFG, quiero lanzar todo el pipeline desde CLI, para poder repetir experimentos de manera directa.
3. Como investigador, quiero entrenar `MLP`, `GRU` y `LSTM` con una interfaz homogénea, para comparar arquitecturas sin fricción operativa.
4. Como investigador, quiero ver qué parámetros son comunes y cuáles son específicos de cada arquitectura, para no mezclar decisiones de modelo con decisiones de experimento.
5. Como investigador, quiero disponer de valores por defecto razonables para cada arquitectura, para arrancar experimentos sin tener que definir todo manualmente.
6. Como investigador, quiero poder sobrescribir hiperparámetros por CLI, para explorar variantes controladas.
7. Como usuario, quiero que cada comando indique claramente sus entradas, salidas y precondiciones, para evitar errores de uso.
8. Como usuario, quiero un comando para generar o registrar datasets desde telemetría persistida, para separar obtención de datos y entrenamiento.
9. Como usuario, quiero un comando para entrenar una sola arquitectura, para iterar rápido sobre una hipótesis concreta.
10. Como usuario, quiero un comando para entrenar las tres arquitecturas con la misma base experimental, para obtener una comparación justa.
11. Como usuario, quiero inspeccionar el contenido de un checkpoint, para saber con qué features, ventanas, seeds y normalización fue entrenado.
12. Como usuario, quiero cargar un checkpoint ya entrenado en el simulador sin escribir código adicional, para validar comportamiento de vuelo completo.
13. Como investigador, quiero ejecutar benchmark homogéneo clásico vs `MLP` vs `GRU` vs `LSTM`, para obtener una comparación reproducible.
14. Como investigador, quiero separar benchmark principal y robustez OOD, para no mezclar selección con evaluación fuera de distribución.
15. Como investigador, quiero que el benchmark guarde trazas y tiempos de inferencia, para analizar precisión, suavidad y coste computacional.
16. Como autor del TFG, quiero un reporte consolidado con tabla, figuras y selección de modelo, para incorporar resultados a la memoria.
17. Como autor del TFG, quiero una convención fija de carpetas y nombres de artefactos, para localizar resultados sin ambigüedad.
18. Como desarrollador, quiero preservar el contrato actual del controlador, para no romper runner, dinámica ni telemetría.
19. Como desarrollador, quiero reutilizar el pipeline interno actual detrás de la CLI, para evitar duplicación de lógica.
20. Como desarrollador, quiero validar por CLI combinaciones de parámetros inválidas, para fallar pronto y con mensajes claros.
21. Como investigador, quiero registrar seeds, split, modo de features y ventana temporal en cada ejecución, para garantizar trazabilidad.
22. Como investigador, quiero que el flujo deje claro que el control usa observación y la evaluación usa estado verdadero, para no introducir ambigüedad metodológica.
23. Como tutor o revisor, quiero leer una guía operativa única del control neuronal, para entender el experimento sin navegar documentos dispersos.
24. Como usuario nuevo del proyecto, quiero empezar con un recorrido mínimo reproducible, para verificar rápido que el pipeline funciona.
25. Como usuario avanzado, quiero lanzar ejecuciones con parámetros explícitos y artefactos versionados, para realizar campañas experimentales serias.
26. Como autor del TFG, quiero documentar las tres arquitecturas bajo la misma plantilla conceptual, para explicar mejor similitudes y diferencias.
27. Como desarrollador, quiero distinguir artefactos intermedios de artefactos finales, para evitar confundir dataset, checkpoints, benchmark y reporte.
28. Como investigador, quiero poder reconstruir qué comando generó cada resultado, para soportar auditoría experimental.
29. Como desarrollador, quiero tests que prueben el flujo observable de la CLI, para proteger la experiencia de uso además de la lógica interna.
30. Como autor del TFG, quiero una capa operable clara sobre el control neuronal, para que el valor del trabajo no dependa de conocimiento tácito.

## Implementation Decisions

- La solución reutilizará el pipeline ya existente de dataset, entrenamiento, benchmark y reporting; no se reescribirá la lógica principal de aprendizaje.
- La mejora principal será una superficie pública de operación, no una nueva familia de controladores.
- La CLI del simulador se ampliará con un espacio de comandos específico para control neuronal, con etapas separadas para dataset, entrenamiento, benchmark, reporte e inspección.
- La experiencia CLI deberá permitir tanto ejecutar una arquitectura concreta como correr un flujo comparativo completo con las tres arquitecturas.
- El contrato de integración con el runner seguirá siendo el del controlador actual que devuelve `VehicleCommand`.
- Las tres arquitecturas compartirán una terminología común para semillas, modo de features, split, paths de entrada y paths de salida.
- Los parámetros específicos de arquitectura deberán presentarse de forma explícita y separada:
  - `MLP`: tamaño de ventana, capas ocultas
  - `GRU`: tamaño de ventana, tamaño oculto, número de capas, dropout
  - `LSTM`: tamaño de ventana, tamaño oculto, número de capas, dropout
- La CLI deberá exponer presets reproducibles por arquitectura y permitir overrides puntuales sin romper trazabilidad.
- Cada ejecución de entrenamiento deberá persistir:
  - checkpoint del modelo
  - resumen legible del checkpoint
  - configuración efectiva de entrenamiento
  - métricas de train y validation
- Cada benchmark deberá persistir:
  - configuración efectiva del benchmark
  - checkpoints usados
  - métricas por escenario
  - trazas comparativas
  - tiempos de inferencia en CPU
- Cada reporte deberá persistir:
  - tabla consolidada
  - selección del mejor modelo
  - figuras comparativas
  - resumen narrativo breve del resultado
- La solución deberá fijar una convención de artefactos por ejecución para que el usuario pueda localizar con claridad dataset, checkpoints, benchmark y reportes.
- La solución deberá fijar una convención documental que explique:
  - qué ve la política
  - qué predice la política
  - qué significa cada parámetro principal
  - cómo ejecutar cada etapa
  - cómo interpretar los artefactos finales
- Se añadirá un comando o modo de inspección para checkpoints y resultados, pensado para lectura rápida por CLI.
- La documentación operativa no dependerá de que el usuario lea tests o código fuente para deducir el flujo correcto.
- La solución deberá mantener la separación metodológica actual entre benchmark principal y batería OOD.
- La solución deberá dejar claro qué decisiones son compartidas por las tres arquitecturas y cuáles son particulares de una sola.
- El flujo mínimo recomendado deberá poder ejecutarse sin escribir scripts Python externos.

### Major Modules

- Módulo de CLI neuronal: traduce comandos públicos a operaciones reproducibles del pipeline interno.
- Módulo de configuración de ejecución: resuelve parámetros efectivos, presets, seeds y rutas de artefactos.
- Módulo de dataset operable: formaliza la carga o construcción de episodios desde telemetría persistida para uso desde CLI.
- Módulo de entrenamiento operable: encapsula entrenamiento por arquitectura y persistencia de artefactos.
- Módulo de inspección de checkpoints: resume metadatos de un modelo entrenado en formato legible.
- Módulo de benchmark operable: ejecuta comparación homogénea con baseline clásico y candidatos neuronales.
- Módulo de reporting operable: genera resultados listos para análisis académico y lectura rápida.
- Módulo de documentación de uso: describe el flujo recomendado, parámetros, ejemplos de ejecución y lectura de resultados.

### Recommended CLI Experience

- Un mismo comando raíz de simulador debe agrupar el flujo neuronal.
- Deben existir comandos separados para:
  - preparar o registrar dataset
  - entrenar una arquitectura
  - entrenar las tres arquitecturas
  - inspeccionar checkpoints
  - ejecutar benchmark principal
  - ejecutar benchmark OOD
  - generar reporte final
- La ayuda de CLI debe documentar defaults, parámetros y artefactos generados.
- Los mensajes por consola deben indicar qué etapa se está ejecutando, qué configuración efectiva se usa y dónde quedan los artefactos.

## Testing Decisions

- Una buena prueba debe validar comportamiento observable del flujo neuronal, no detalles internos de implementación de `argparse`, `torch` o estructuras privadas.
- La nueva CLI neuronal debe probarse extremo a extremo con entradas pequeñas y deterministas.
- Las pruebas deben verificar que cada comando genera los artefactos esperados y que esos artefactos son legibles por la siguiente etapa del pipeline.
- Las pruebas deben comprobar que la configuración efectiva persistida coincide con los argumentos recibidos por CLI.
- Las pruebas deben validar mensajes de error claros ante:
  - arquitectura no soportada
  - parámetros incompatibles
  - ausencia de artefactos requeridos
  - rutas inválidas o incompletas
- Las pruebas deben cubrir el flujo mínimo reproducible:
  - dataset
  - entrenamiento
  - benchmark
  - reporte
- Las pruebas deben cubrir tanto ejecución por arquitectura individual como ejecución comparativa de las tres arquitecturas.
- Las pruebas deben comprobar que el resumen de checkpoint expone los campos necesarios para auditoría experimental.
- Las pruebas deben comprobar que benchmark principal y benchmark OOD quedan separados también en la capa CLI y documental.
- Las pruebas deben seguir el estilo ya asentado en el repositorio: datasets pequeños, escenarios deterministas y verificación de invariantes externos.
- Los módulos prioritarios para test son:
  - CLI neuronal
  - resolución de configuración efectiva
  - inspección de checkpoints
  - encadenamiento dataset -> train -> benchmark -> report

## Out of Scope

- Añadir nuevas arquitecturas más allá de `MLP`, `GRU` y `LSTM`.
- Rediseñar el contrato principal del runner o de `VehicleCommand`.
- Cambiar la frontera metodológica de observación frente a estado verdadero.
- Reemplazar la evaluación actual por una interfaz gráfica interactiva.
- Introducir reinforcement learning, fine-tuning online o control híbrido en esta iteración.
- Resolver despliegue embebido, tiempo real duro o integración con hardware.
- Realizar una búsqueda masiva de hiperparámetros.
- Reorganizar toda la documentación del TFG más allá de lo necesario para explicar el flujo operable.

## Further Notes

- Este PRD complementa la PRD de fase 2 existente. No redefine el objetivo científico del control neuronal; redefine cómo se usa de manera clara y reproducible.
- El repositorio ya contiene la mayor parte de la lógica interna necesaria. La oportunidad principal está en convertir esa capacidad en experiencia operable y documentación de uso.
- La mejora tiene valor académico directo: reduce ambigüedad metodológica, aumenta repetibilidad y facilita explicar el trabajo ante tutor y tribunal.
- La definición de CLI y artefactos debe mantenerse simple. Si la herramienta se vuelve demasiado flexible desde el primer día, volverá a aparecer fricción de uso.
- La documentación final de esta mejora debe incluir un recorrido mínimo recomendado y un recorrido completo comparativo para las tres arquitecturas.
