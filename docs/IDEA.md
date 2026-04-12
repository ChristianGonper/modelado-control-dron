
# Modelado y Desarrollo de un Sistema de Control Inteligente para un Dron Multirotor

Este documento describe la visión, objetivos y fases de desarrollo para el Trabajo de Fin de Grado (TFG) de Ingeniería Aeroespacial a alto nivel.

## 1. Visión General
El proyecto consiste en el desarrollo de un sistema de control de trayectorias para un dron multirotor basado en redes neuronales. Se utilizará una aproximación en fases, comenzando por un entorno de simulación realista y culminando en la implementación o validación con hardware real.

*   **Plataforma Física:** [LiteWing ESP32-S3](Dron_fisico.md)
*   **Enfoque:** Control de trayectorias mediante arquitecturas de aprendizaje inteligente.

---

## 2. Roadmap del Proyecto

### Fase 1: Desarrollo del Simulador (Prioridad Actual)
Creación de un entorno de simulación modular en Python, inspirado en [rotorpy](https://github.com/spencerfolk/rotorpy), pero simplificado y optimizado para este TFG.

*   **Modelo Físico:** Dinámica de cuerpo rígido (6 DOF) con un modelo de motores simplificado y efectos aerodinámicos moderados.
*   **Sistema de Control Base:**
    *   Control en cascada: Bucle interno (estabilización) y bucle externo (trayectorias) mediante PID.
    *   Arquitectura "Plug & Play" para intercambiar controladores fácilmente.
*   **Gestión de Datos:** Capacidad para exportar telemetría en formatos `CSV`, `JSON` y `Numpy`.
*   **Visualización:** Herramientas de visualización simple en 2D y 3D (post-procesado).

### Fase 2: Control Inteligente en Simulación
Sustitución del control de trayectorias tradicional por redes neuronales.

*   Exploración de diversas arquitecturas de redes neuronales.
*   Entrenamiento basado en los datos generados por el simulador de la Fase 1.
*   Validación de la precisión y robustez en el seguimiento de trayectorias predefinidas.

### Fase 3: Integración con Hardware Real
Puente entre la simulación y el mundo real.

*   Captura de datos reales del LiteWing ESP32-S3.
*   Identificación de sistemas para ajustar los parámetros del simulador 
*   Validación cruzada de resultados.

---

## 3. Especificaciones Técnicas y Diseño

### Entradas de Control
El sistema de control actuará sobre:
*   **Thrust Colectivo:** Empuje total aplicado al centro de masa.
*   **Torques del Cuerpo:** Momentos en los ejes X, Y, Z para el control de actitud.

### Arquitectura de Software
*   **Modularidad:** El simulador debe permitir añadir nuevas dinámicas, perturbaciones o trayectorias sin reconstruir el núcleo.
*   **Flujo de Trabajo:** Documentación exhaustiva del modelo matemático y el flujo de datos.

---

## 4. Referencias y Herramientas
*   **Base de Ideas:** [RotorPy](https://github.com/spencerfolk/rotorpy) (Spencer Folk).
*   **Hardware:** Wiki de [LiteWing ESP32-S3](Dron_fisico.md).
*   **Metodología:** Uso de skills internas para la gestión de tareas y documentación técnica.