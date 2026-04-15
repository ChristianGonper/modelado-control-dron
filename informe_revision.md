# Informe de Revisión: Simulador Multirotor

Este documento detalla los resultados de la revisión en profundidad del proyecto `simulador-multirotor`. Se abordan tres dimensiones principales: la física e ingeniería, la arquitectura e implementación de alto nivel, y la documentación y metodología.

## 1. Física e Ingeniería

### Puntos Fuertes
- **Integración Numérica Robusta**: El uso del método de Runge-Kutta de cuarto orden (RK4) en `RigidBody6DOFDynamics` es una decisión ingenieril madura. Evita la rápida divergencia y errores acumulativos inherentes al método de Euler (muy común en simuladores iniciales).
- **Tratamiento de la Actitud (SO(3))**: El empleo de cuaterniones para la orientación del vehículo, integrando cinemáticamente a partir de las derivadas de velocidad angular e incluyendo el acoplamiento giroscópico, previene el *gimbal lock* y mantiene el estado en la variedad correspondiente de forma limpia, normalizando en cada paso.
- **Separación de Estados Real y Observado**: La distinción entre `true_state` y `observed_state` es fundamental para simuladores enfocados en robótica (sim-to-real). Permite introducir modelos de ruido en los sensores sin alterar las verdaderas dinámicas del vuelo.
- **Modelado Aerodinámico y Perturbaciones**: El modelo de viento utiliza un proceso discreto de Ornstein-Uhlenbeck (OU), lo cual es brillante porque garantiza la estabilidad de la varianza estadística del viento independientemente de variaciones en el `dt` de simulación. Además, la inclusión de arrastre parásito y pérdida inducida de empuje en *hover* proporciona una complejidad aerodinámica suficiente sin penalizar el rendimiento.
- **Jerarquía de Control Aislada**: La abstracción desde un `VehicleIntent` (fuerza global/torque) hacia mandos a nivel rotor (`RotorCommand` y Mixer) con dinámicas de primer orden sienta una base excelente para probar actuadores.

### Puntos a Mejorar
- **Aerodinámica Superficial**: Aunque los efectos incluidos son un buen punto de partida, el arrastre parásito y la pérdida en hover están muy simplificados (el "induced term" es un ratio estático dependiente de `max_thrust`). Para escenarios agresivos, faltan interacciones aerodinámicas de rotores (flujo inducido cruzado, Blade Element Theory) o efecto suelo.
- **Límites Físicos del Actuador**: La dinámica del rotor es de primer orden, pero no se simulan efectos como la desaturación eléctrica, límites de corriente de la batería y la caída de tensión en los ESCs, que a menudo son los verdaderos limitantes en maniobras agresivas de multirotores reales.
- **Controlador Base Limitado**: El `CascadedController` actual es rudimentario ("no es de alto rendimiento", como señala la documentación). Sería beneficioso implementar un controlador LQR o INDI (Incremental Nonlinear Dynamic Inversion) como verdadero estándar geométrico contra el cual comparar futuras políticas de control inteligente (ej. redes neuronales).

---

## 2. Implementación de Alto Nivel

### Puntos Fuertes
- **Diseño Orientado a Contratos**: La estructura central en `core/contracts.py` y el uso intensivo de `dataclasses` (usando `frozen=True` y `slots=True`) previene fallos por mutación de estado accidental y facilita enormemente la depuración. Además evita dependencias circulares, logrando un acoplamiento bajísimo.
- **El Patrón "Tracer Bullet"**: El orquestador o *runner* principal está fuertemente desacoplado de las trayectorias y los controladores. Este marco "plug-and-play" hace trivial el intercambio del PID por un controlador basado en PyTorch (MLP), algo clave para el objetivo de Machine Learning del proyecto.
- **Reproducibilidad Garantizada**: Se ha hecho un esfuerzo consciente para sembrar (*seed*) todas las fuentes de estocasticidad (inyección de ruido, viento), lo que garantiza que las simulaciones sean 100% deterministas y reproducibles, algo crítico al entrenar modelos y recolectar datasets empíricos.
- **Gestión de Datos y Telemetría**: El subsistema de telemetría expone datos estructurados en NumPy, JSON y CSV. La separación del tiempo físico (`physics_dt_s`), tiempo de control (`control_dt_s`) y de muestreo de telemetría (`telemetry_dt_s`) permite emular restricciones de hardware de microcontroladores reales.

### Puntos a Mejorar
- **Falta de Validación Estricta de Tipos en Tiempo de Ejecución**: Las `dataclasses` utilizan métodos dunder como `__post_init__` con validaciones de *coerción* manuales (ej. `_coerce_float`). Reemplazar esto con librerías como **Pydantic** podría reducir considerablemente el "boilerplate", validando tipos, límites e incluso serializando configuraciones desde archivos JSON o YAML nativamente.
- **Visualización Puramente Estática**: Actualmente la visualización es mediante post-procesamiento (PNGs de Matplotlib). Para un simulador de desarrollo se agradecería muchísimo un renderizado interactivo mínimo (como Foxglove, MeshCat o rerun.io) para visualizar el dron comportándose en el bucle *live*.
- **Configuración JSON en Crecimiento**: A medida que los escenarios crecen en complejidad, crear y mantener diccionarios de configuraciones complejas en JSON se volverá tedioso. Adoptar formatos como YAML e interfaces tipo Builder API o Fluent API simplificará la vida al investigador.

---

## 3. Documentación y Metodología

### Puntos Fuertes
- **ADRs (Architecture Decision Records)**: El uso de ADRs (ej. ADR-009) demuestra una madurez ingenieril superior al promedio en proyectos académicos. Documentan el contexto, las alternativas rechazadas y las consecuencias de cada decisión importante, protegiendo al proyecto de futuras refactorizaciones a ciegas.
- **Roadmap Claro y PRDs Detallados**: La estructuración en fases y los *Product Requirement Documents* aseguran que el proyecto esté alineado con el propósito del TFG. Destaca especialmente que los PRDs incluyen explícitamente secciones "Out of Scope" (fuera de alcance), combatiendo el *scope creep*.
- **Backlog Priorizado y Autoconsciente**: El archivo `backlog_tecnico.md` y `estado_actual_simulador.md` reflejan un profundo conocimiento técnico y honestidad sobre las carencias del sistema, lo cual es la mejor guía posible para colaboraciones de otras personas.

### Puntos a Mejorar
- **Documentación de API y Docstrings**: La documentación a nivel arquitectónico es excelente, pero la de la API del código interno es dispar. Algunas funciones carecen de docstrings detallados que especifiquen las unidades de medida (aunque muchas variables sí las llevan en el sufijo del nombre, como `_rad_s` o `_newton`, lo cual es una gran práctica).
- **Ejemplos Interactivos Ausentes**: Tal como sugiere el propio backlog de forma "Media-Baja", la adición de Jupyter Notebooks interactivos facilitaría la exploración inicial de la telemetría, el comportamiento del viento, o la simple visualización sin obligar al usuario a descifrar la CLI en primer lugar.
