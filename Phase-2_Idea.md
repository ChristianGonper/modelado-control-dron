# Plan de Fase 2 – Control de Trayectorias mediante Redes Neuronales

**Versión:** 0.3  
**Fecha:** 15/04/2026  
**Estado:** 
## 1. Objetivos claros de esta fase
- Desarrollar y validar **controladores neuronales** (policy networks) capaces de realizar seguimiento preciso de trayectorias complejas en el simulador de dron multirrotor (6-DoF).
- Probar y comparar tres arquitecturas: MLP (baseline), LSTM y GRU.
- Demostrar que el controlador neuronal es capaz de seguir trayectorias exigentes (espirales 3D, Lissajous, figuras-8, maniobras agresivas, etc.) con precisión y robustez frente a perturbaciones externas.
- Comparar su rendimiento frente al controlador clásico en cascada (PID + mixer) actual.
- Generar evidencia cuantitativa y cualitativa para justificar la selección del mejor modelo en el TFG.

**Éxito de fase:** Controlador neuronal funcional, entrenado y evaluado, que iguale o supere al clásico en métricas de seguimiento de trayectoria. Prueba completamente reproducible y documentada.

## 2. Estrategia de Generación de Datos
- Utilizar el **controlador clásico existente** como “expert” para generar datos de demostración (Imitation Learning / Behavioral Cloning).
- Ejecutar múltiples trayectorias exigentes con diferentes perturbaciones: viento variable (constante + ráfagas), niveles de batería, saturación de actuadores.
- Loguear a 100-200 Hz:
  - Estado actual del dron (posición, velocidad lineal, Euler, velocidades angulares).
  - Referencia de trayectoria (posición/velocidad deseada, yaw deseado).
  - Acciones de control aplicadas por el controlador clásico (thrust total + momentos o directamente PWM por motor).
- **Volumen objetivo**: mínimo 50-100 episodios de 60-120 s cada uno.
- **División train/val/test**: por trayectorias completas (time-series split) para evitar data leakage.

*(Perturbaciones solo externas por ahora; ruido de sensores queda como opción abierta).*

## 3. Arquitecturas a probar
| Arquitectura | Rol                  | Ventajas esperadas                          | Desventajas                     |
|--------------|----------------------|---------------------------------------------|---------------------------------|
| **MLP**      | Baseline             | Simple, rápido de entrenar e inferir        | No captura memoria temporal     |
| **LSTM**     | Candidata principal  | Excelente para dependencias temporales      | Mayor coste computacional       |
| **GRU**      | Candidata eficiente  | Balance entre rendimiento y velocidad       | Ligeramente menor capacidad     |

**Input**: Estado actual + referencia de trayectoria (ventana temporal).  
**Output**: Comandos de control (thrust total + momentos de torque o directamente PWM por motor, según lo que más se integre con el mixer existente).  

*(Ampliación a Transformer ligero o TCN queda explícitamente como extensión futura).*

## 4. Preparación y preprocesamiento de datos
- Ventanas temporales (sequence length): 10, 20, 50 pasos (a tunear).
- Normalización/estandarización por variable.
- División temporal estricta.
- Enfoque principal de entrenamiento: **supervisado (Behavioral Cloning)**.

## 5. Proceso de entrenamiento y experimentación (PyTorch)
- Framework: PyTorch (Lightning recomendado para estructurar).
- Hiperparámetros clave: learning rate, batch size, hidden size, capas, sequence length, dropout.
- Entrenamiento con early-stopping.
- Posible fine-tuning posterior con RL si el tiempo lo permite (línea futura).

## 6. Criterios de evaluación y análisis comparativo

**Métricas principales (todas obligatorias):**
- **RMSE** y **MAE** de error de seguimiento (posición x,y,z y actitud).
- **R²** (Coefficient of Determination) y **correlación de Pearson** entre trayectoria deseada y real.
- Error de seguimiento integral (IAE / ISE).
- Suavidad de las señales de control (derivada de thrust y torques).
- Robustez a perturbaciones (test con viento más fuerte o no visto en entrenamiento).
- Tiempo de inferencia medio (ms por paso) en CPU.
- Estabilidad del vuelo (oscilaciones, overshoot, settling time).
- Comparación directa: Controlador clásico vs MLP vs LSTM vs GRU en las mismas trayectorias de test (nunca vistas durante entrenamiento).

**Presentación de resultados:**
- Tabla comparativa consolidada.
- Gráficos de trayectoria real vs deseada (vista 3D), evolución temporal de errores, señales de control, etc.
- Análisis cualitativo de ventajas/desventajas (ej. mejor manejo de saturación o viento).

**Criterio de selección:** Mejor balance entre precisión de seguimiento, suavidad, robustez y velocidad de inferencia.

## 7. Hoja de ruta posterior a la fase
1. Integración del controlador neuronal seleccionado como componente intercambiable en el simulador (junto al clásico).
2. Evaluación comparativa exhaustiva y documentación en el TFG.
3. Preparación para sim-to-real y posibles extensiones (MPC híbrido, RL fine-tuning, etc.).
4. Línea futura: optimización de trayectorias o control predictivo con el controlador neuronal.

**Riesgos y mitigaciones:**
- Overfitting al comportamiento del controlador clásico → alta diversidad de trayectorias y perturbaciones.
- Inestabilidad en rollout → entrenamiento con ventanas temporales y posible regularización.
- Tiempo de inferencia elevado → priorizar GRU si LSTM es demasiado lenta.

## Checklist de tareas para completar Fase 2
- [ ] Generar dataset de demostraciones con controlador clásico.
- [ ] Implementar pipeline de preprocesamiento y DataLoaders.
- [ ] Entrenar y evaluar MLP, LSTM y GRU.
- [ ] Comparar contra controlador clásico y documentar resultados.
- [ ] Integrar el mejor modelo como módulo intercambiable en el simulador (prueba funcional).
- [ ] Actualizar documentación del proyecto (ADR + sección en memoria del TFG).
