# PRD: Simulador modular para control inteligente de dron multirotor

## Problem Statement

El TFG necesita una base experimental fiable para diseñar, entrenar y validar un sistema de control de trayectorias para un dron multirotor. Ahora mismo la visión del proyecto está definida a alto nivel, pero falta concretar un producto intermedio que permita iterar con rapidez, generar datos consistentes y comparar estrategias de control antes de pasar a redes neuronales o a hardware real.

Sin ese simulador, el desarrollo del controlador inteligente queda bloqueado por varios problemas: no existe un entorno reproducible para validar trayectorias, no hay una interfaz estable para intercambiar controladores, no se ha fijado un formato común de telemetría y no hay una base técnica clara para enlazar la simulación con el dron LiteWing ESP32-S3 en fases posteriores.

El problema, por tanto, no es solo "simular un dron", sino disponer de un simulador suficientemente realista, modular y trazable como para servir como plataforma de experimentación del TFG durante todas las fases del trabajo.

## Solution

Se desarrollará un simulador modular en Python para un dron multirotor de 6 grados de libertad, inspirado en RotorPy pero reducido al alcance del TFG. El simulador modelará la dinámica de cuerpo rígido, un modelo simplificado de motores, perturbaciones y efectos aerodinámicos moderados, y expondrá una arquitectura plug-and-play para cambiar controladores, trayectorias y escenarios sin modificar el núcleo.

El producto incluirá un controlador base en cascada con PID para estabilización y seguimiento de trayectorias, un sistema de ejecución de escenarios reproducibles, exportación de telemetría en `CSV`, `JSON` y `NumPy`, y visualización 2D/3D orientada a post-procesado. Además, la solución dejará preparada la interfaz necesaria para que, en una segunda fase, un controlador inteligente pueda sustituir al controlador externo tradicional sin rediseñar toda la plataforma.

La simulación no pretende replicar toda la complejidad aerodinámica ni todos los detalles del firmware del LiteWing. Su objetivo es maximizar utilidad experimental, claridad arquitectónica y capacidad de validación para el TFG.

## User Stories

1. Como estudiante investigador del TFG, quiero ejecutar simulaciones reproducibles de un multirotor, para poder comparar controladores en igualdad de condiciones.
2. Como desarrollador del simulador, quiero definir el vehículo mediante parámetros físicos explícitos, para poder ajustar masa, inercias, geometría y límites de actuadores sin reescribir el motor de simulación.
3. Como desarrollador del controlador, quiero recibir un estado del dron bien definido, para diseñar leyes de control sin depender de detalles internos del integrador.
4. Como desarrollador del controlador, quiero enviar comandos de thrust colectivo y torques en ejes cuerpo, para desacoplar la lógica de control del modelo concreto de motores.
5. Como usuario del simulador, quiero intercambiar fácilmente entre controlador PID y futuros controladores inteligentes, para reutilizar el mismo entorno experimental.
6. Como investigador, quiero definir trayectorias de referencia parametrizables, para evaluar seguimiento en distintos perfiles de misión.
7. Como investigador, quiero ejecutar vuelos estacionarios, escalones, circunferencias y trayectorias temporizadas, para cubrir casos de prueba básicos y comparables.
8. Como investigador, quiero añadir perturbaciones externas controladas, para estudiar robustez frente a viento, ruido o errores de modelo.
9. Como desarrollador, quiero encapsular la dinámica del vehículo en un módulo profundo y testeable, para poder validar el modelo físico de forma aislada.
10. Como desarrollador, quiero encapsular la lógica de control en interfaces simples, para poder sustituir implementaciones sin tocar el bucle principal de simulación.
11. Como desarrollador, quiero separar la generación de referencias de la dinámica y del control, para evitar acoplamientos innecesarios.
12. Como usuario del simulador, quiero fijar condiciones iniciales configurables, para reproducir escenarios nominales y perturbados.
13. Como usuario del simulador, quiero seleccionar paso de integración y horizonte temporal, para balancear coste computacional y fidelidad.
14. Como investigador, quiero registrar la telemetría completa de estados, referencias, errores y acciones de control, para analizar rendimiento offline.
15. Como investigador, quiero exportar resultados en `CSV`, para analizarlos con herramientas de hoja de cálculo o scripts sencillos.
16. Como investigador, quiero exportar resultados en `JSON`, para compartir ejecuciones y metadatos de escenario de forma legible.
17. Como investigador, quiero exportar resultados en `NumPy`, para alimentar pipelines de entrenamiento y análisis numérico.
18. Como usuario del simulador, quiero visualizar trayectorias y actitudes en 2D, para hacer inspección rápida de resultados.
19. Como usuario del simulador, quiero visualizar trayectorias en 3D, para validar cualitativamente maniobras y orientación.
20. Como investigador, quiero que la visualización esté desacoplada de la simulación, para no penalizar barridos de experimentos.
21. Como investigador, quiero poder repetir un experimento con la misma semilla y configuración, para obtener resultados comparables.
22. Como investigador, quiero guardar la configuración del escenario junto con la telemetría, para mantener trazabilidad experimental.
23. Como desarrollador, quiero una API clara para observaciones del simulador, para conectar en el futuro modelos de aprendizaje automático.
24. Como desarrollador, quiero una API clara para acciones de control, para evitar ambigüedad entre mandos de alto nivel y actuadores.
25. Como investigador, quiero medir métricas de seguimiento de trayectoria, para cuantificar error, sobreoscilación y esfuerzo de control.
26. Como investigador, quiero comparar varias ejecuciones bajo una misma batería de escenarios, para justificar decisiones de diseño.
27. Como estudiante, quiero documentar el modelo matemático y el flujo de datos, para respaldar la memoria del TFG y facilitar revisión académica.
28. Como desarrollador, quiero que el simulador sea suficientemente simple para mantenerlo dentro del alcance del TFG, para no quedar bloqueado en complejidad no esencial.
29. Como investigador, quiero introducir ruido de sensor configurable, para aproximar condiciones más realistas cuando sea útil.
30. Como investigador, quiero poder desactivar perturbaciones y ruido, para validar primero el comportamiento nominal.
31. Como desarrollador, quiero que el bucle de simulación sea independiente de los controladores concretos, para preservar extensibilidad.
32. Como futuro integrador con hardware, quiero que los parámetros del modelo puedan reajustarse con datos reales, para reducir la brecha sim-to-real.
33. Como futuro integrador con hardware, quiero que la estructura de telemetría sea compatible conceptualmente con datos del LiteWing, para facilitar validación cruzada.
34. Como desarrollador, quiero definir límites de saturación y restricciones físicas, para evitar resultados no plausibles.
35. Como investigador, quiero generar datasets consistentes a partir de muchas ejecuciones, para entrenar redes neuronales en la siguiente fase.
36. Como investigador, quiero aislar el controlador externo del interno, para poder sustituir solo el lazo de trayectorias por una red neuronal.
37. Como estudiante, quiero un conjunto de escenarios de referencia bien documentados, para sustentar comparativas en la memoria.
38. Como desarrollador, quiero una organización modular del código, para que nuevas dinámicas, perturbaciones o trayectorias se añadan sin rehacer el núcleo.
39. Como revisor académico, quiero entender qué simplificaciones se han adoptado y por qué, para evaluar la validez del simulador para el objetivo del TFG.
40. Como usuario del sistema, quiero una forma simple de lanzar una simulación completa de extremo a extremo, para reducir fricción en el trabajo diario.

## Implementation Decisions

- El producto de esta PRD es la Fase 1 del roadmap: un simulador orientado a experimentación, no una réplica completa del firmware del dron real.
- El lenguaje base será Python, coherente con la necesidad de análisis numérico, generación de datasets y futura integración con control inteligente.
- El modelo físico central será un módulo de dinámica de cuerpo rígido 6 DOF con estado continuo del vehículo, responsable de evolucionar posición, velocidad, actitud y velocidades angulares.
- La interfaz del modelo aceptará entradas de thrust colectivo y torques en ejes cuerpo, manteniendo desacoplado el controlador de los detalles de asignación a motores.
- El modelo incluirá un subsistema simplificado de actuadores/motores para capturar al menos límites, saturación y una dinámica básica suficiente para evitar respuestas idealizadas.
- El primer modelo aerodinámico será deliberadamente sencillo y priorizará los efectos con mayor impacto práctico para el TFG: arrastre parásito y un término simplificado de efectos inducidos, con especial atención al régimen de hover.
- Los efectos aerodinámicos se implementarán de forma incremental y parametrizable, de modo que puedan activarse, desactivarse o recalibrarse sin alterar el núcleo del simulador.
- La arquitectura se organizará alrededor de módulos profundos con responsabilidades claras: dinámica del vehículo, interfaz de control, generador de trayectorias, motor de escenarios, telemetría/exportación y visualización.
- El controlador base será en cascada, con un lazo interno de estabilización y un lazo externo de seguimiento de trayectorias mediante PID.
- La interfaz de control será plug-and-play: cualquier controlador que cumpla el contrato de entradas observables y salidas de mando podrá conectarse al bucle de simulación.
- La generación de trayectorias se implementará como un módulo independiente capaz de producir referencia temporal de posición, velocidad, yaw y, cuando sea necesario, derivadas auxiliares.
- El contrato de trayectorias se fijará sobre una interfaz estable en la que cada generador de referencia reciba al menos tiempo de simulación y su configuración parametrizada, y devuelva una referencia estructurada con posición deseada, velocidad deseada, aceleración deseada opcional, yaw deseado y metadatos mínimos de validez temporal.
- El motor de simulación será responsable de orquestar integración temporal, lectura de referencia, cálculo de control, aplicación de perturbaciones y captura de telemetría.
- La configuración de escenarios deberá incluir como mínimo parámetros del vehículo, condiciones iniciales completas, duración, paso temporal, trayectoria seleccionada, parámetros de trayectoria, perturbaciones, semilla y opciones de exportación.
- El sistema de escenarios debe aceptar tanto trayectorias incluidas de forma nativa en el simulador como trayectorias proporcionadas externamente mediante el contrato definido para generadores de referencia.
- El esquema mínimo de configuración de escenarios quedará organizado en bloques conceptuales: definición del vehículo, estado inicial, configuración temporal de la simulación, definición de trayectoria, perturbaciones/ruido, opciones de telemetría y exportación, y metadatos del experimento.
- El bloque de estado inicial incluirá posición, orientación, velocidades lineales y velocidades angulares, con valores por defecto razonables para simplificar escenarios nominales.
- El bloque de trayectoria incluirá un identificador de tipo, parámetros propios de la familia seleccionada, duración prevista y cualquier información necesaria para distinguir entre trayectorias nativas y trayectorias suministradas externamente.
- El bloque temporal incluirá al menos horizonte total, paso de integración y, si fuera distinto, frecuencia de muestreo de telemetría.
- El bloque de perturbaciones permitirá activar o desactivar viento, ruido y efectos aerodinámicos configurables sin cambiar el contrato general del escenario.
- El bloque de exportación permitirá seleccionar formatos de salida, nivel de detalle de telemetría y metadatos asociados a cada ejecución.
- Cada ejecución guardará tanto la telemetría como los metadatos del escenario para asegurar reproducibilidad y trazabilidad.
- La telemetría mínima registrará tiempo, estado real, referencia, error de seguimiento, acción de control y eventos de saturación o perturbación relevantes.
- La exportación soportará `CSV`, `JSON` y `NumPy` como formatos nativos del producto.
- La visualización será de post-procesado, no un requisito de tiempo real; se prioriza la claridad del análisis sobre la animación interactiva.
- El diseño debe favorecer el reemplazo futuro del controlador externo PID por una red neuronal, idealmente sin modificar ni el modelo dinámico ni el formato de dataset.
- La plataforma debe admitir calibración posterior con datos del LiteWing ESP32-S3, pero esa calibración no es prerequisito para completar esta fase.
- Se asume inicialmente un único tipo de vehículo multirotor compatible con la plataforma física objetivo; el soporte genérico para múltiples configuraciones queda fuera salvo que no incremente mucho la complejidad.
- Se asume que la validación del simulador será comparativa y experimental, no una certificación de alta fidelidad física.
- El conjunto mínimo de trayectorias nativas para la primera versión incluirá referencias básicas suficientes para validación y memoria: rectas, círculos, espirales, curvas paramétricas sencillas y al menos una trayectoria de tipo Lissajous.
- La configuración inicial del escenario debe permitir seleccionar posición inicial, orientación inicial, velocidades lineales y angulares iniciales y cualquier otro parámetro básico necesario para arrancar la simulación de forma controlada.

### Módulos principales propuestos

- Módulo de parámetros del vehículo: define masa, inercias, límites, constantes de actuador y parámetros aerodinámicos.
- Módulo de dinámica y actuadores: integra la evolución del vehículo a partir del estado actual y los mandos aplicados.
- Módulo de controladores: aloja el PID en cascada y futuras implementaciones bajo el mismo contrato.
- Módulo de trayectorias y referencias: genera referencias temporales reutilizables.
- Módulo de escenarios/runner: ejecuta simulaciones completas y garantiza reproducibilidad.
- Módulo de telemetría y exportación: normaliza el registro y la salida a formatos de análisis.
- Módulo de visualización y análisis: produce gráficas y representaciones 2D/3D desacopladas del núcleo.
- Módulo de métricas: calcula errores de seguimiento y otras medidas comparables entre ejecuciones.

## Testing Decisions

- Una buena prueba validará comportamiento observable y contratos del sistema, no detalles internos del integrador ni constantes privadas.
- El mayor peso de tests debe recaer sobre módulos profundos y estables: dinámica, controladores, runner de escenarios, métricas y exportación.
- El módulo de dinámica debe probar conservación y plausibilidad física básica bajo entradas conocidas, respuesta ante gravedad, saturaciones y consistencia dimensional de estados y mandos.
- El módulo de controladores debe probar estabilidad y dirección cualitativa de la corrección en escenarios controlados, así como manejo de límites y casos frontera.
- El módulo de trayectorias debe probar continuidad temporal, valores esperados en puntos clave y validez de referencias generadas.
- El módulo de trayectorias debe cubrir al menos las familias mínimas definidas en esta PRD y verificar que sus parámetros producen geometrías y perfiles temporales válidos.
- El módulo de trayectorias debe validar el contrato común de referencia, incluyendo campos obligatorios, manejo de horizontes temporales y comportamiento consistente cuando una trayectoria agota su validez.
- El runner de escenarios debe probar reproducibilidad con la misma configuración y semilla, y consistencia entre configuración de entrada y artefactos generados.
- El runner de escenarios debe probar la correcta carga tanto de trayectorias nativas como de trayectorias externas que cumplan el contrato de referencia.
- El runner de escenarios debe probar la validación del esquema de configuración mínimo, así como valores por defecto razonables y errores claros ante configuraciones incompletas o inconsistentes.
- El módulo de exportación debe probar esquema, nombres de campos, integridad de tamaños y compatibilidad de los formatos `CSV`, `JSON` y `NumPy`.
- El módulo de métricas debe probar resultados correctos para series sintéticas donde el error esperado pueda calcularse manualmente.
- La visualización requerirá pruebas ligeras centradas en generación de artefactos y uso correcto de telemetría, evitando tests frágiles basados en píxeles salvo necesidad clara.
- Como el repositorio todavía no contiene una base de tests comparable, la referencia de prior art será el patrón general de pruebas de comportamiento para software científico: fixtures pequeñas, escenarios deterministas y validación de invariantes físicos o contractuales.
- Se priorizarán pruebas unitarias y de integración corta sobre simulaciones largas, para mantener velocidad y fiabilidad del ciclo de desarrollo.

## Out of Scope

- Entrenamiento e integración de redes neuronales en esta primera fase.
- Validación en tiempo real sobre hardware LiteWing o firmware embebido.
- Réplica detallada de todos los sensores, buses, protocolos o peculiaridades del firmware del dron real.
- Modelado aerodinámico de alta fidelidad, turbulencia avanzada o efectos complejos de interacción hélice-estructura.
- Simulación foto-realista o visualización inmersiva.
- Herramientas de operación en vuelo real, control remoto o despliegue embebido.
- Soporte completo para múltiples arquitecturas de aeronaves fuera del multirotor objetivo del TFG.
- Optimización prematura para rendimiento masivo o ejecución distribuida.

## Further Notes

- Esta PRD asume que el primer entregable útil del TFG debe maximizar aprendizaje experimental y generación de datos, no fidelidad absoluta.
- El diseño queda deliberadamente preparado para una transición posterior hacia sim-to-real mediante reajuste de parámetros con telemetría del LiteWing.
- La ausencia de código en el repositorio sugiere que esta PRD debe actuar también como documento de alineación inicial para arquitectura y alcance.
- El nivel inicial de fidelidad aerodinámica queda fijado en un modelo simple, extensible y centrado en arrastre parásito y efectos inducidos relevantes en hover.
- El esquema de escenarios queda orientado a configuración básica pero ampliable, con selección de trayectoria, condiciones iniciales y parámetros experimentales esenciales como punto de partida.
- El conjunto mínimo de trayectorias de referencia obligatorio para la primera versión queda fijado en rectas, círculos, espirales, curvas paramétricas sencillas y Lissajous.

## Anexo: Contrato de Trayectorias

Cada trayectoria, ya sea nativa o externa, debe cumplir un mismo contrato conceptual para que el runner y los controladores permanezcan desacoplados.

- Entrada mínima del generador: tiempo de simulación y configuración parametrizada de la trayectoria.
- Salida mínima de referencia: posición deseada en 3D, velocidad deseada en 3D, yaw deseado y un indicador de validez temporal.
- Salida recomendada: aceleración deseada y metadatos auxiliares para análisis o control feedforward futuro.
- El contrato debe permitir trayectorias temporizadas y trayectorias definidas por parámetros geométricos simples.
- Una trayectoria nativa se identificará por un tipo conocido por el simulador y un conjunto de parámetros validados según su familia.
- Una trayectoria externa deberá adaptarse al mismo contrato de entrada/salida para poder ejecutarse sin excepciones especiales en el runner.
- Si una trayectoria deja de ser válida tras cierto horizonte, el contrato debe definir un comportamiento explícito y uniforme, por ejemplo mantener el último punto, finalizar la simulación o marcar fin de referencia.
- El contrato debe ser suficiente para soportar, en la primera versión, rectas, círculos, espirales, curvas paramétricas sencillas y Lissajous.

## Anexo: Esquema Mínimo de Escenario

Todo escenario debe describirse mediante una configuración ampliable pero con una base común estable.

- Identificación y metadatos del experimento: nombre, descripción opcional, semilla y etiquetas.
- Definición del vehículo: parámetros físicos y límites necesarios para la simulación.
- Estado inicial: posición, orientación, velocidad lineal y velocidad angular.
- Configuración temporal: duración total, paso de integración y frecuencia de registro si difiere del paso de simulación.
- Configuración de trayectoria: tipo de trayectoria, parámetros asociados y origen de la referencia si es nativa o externa.
- Perturbaciones y ruido: activación y parámetros de viento, ruido y términos aerodinámicos configurables.
- Controlador seleccionado: identificador del controlador activo y sus ganancias o parámetros.
- Telemetría y exportación: variables a registrar, formatos de salida y nivel de detalle.
- Criterios de finalización opcionales: fin por tiempo, por agotamiento de referencia o por condición anómala si se decide incorporar más adelante.

Este esquema debe diseñarse para comenzar con configuraciones básicas por defecto, pero sin impedir ampliar campos en fases posteriores ni romper compatibilidad con escenarios ya definidos.
