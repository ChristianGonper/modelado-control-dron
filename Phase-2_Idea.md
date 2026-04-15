# Plan de Fase 2 – Control de Trayectorias mediante Redes Neuronales

**Versión:** 0.4  
**Fecha:** 15/04/2026  
**Estado:**

## 1. Objetivos claros de esta fase
- Desarrollar y validar **controladores neuronales** (MLP, LSTM y GRU) para seguimiento preciso de trayectorias complejas en el simulador de dron multirrotor (6-DoF).
- **Integrar cada red neuronal directamente con el simulador** para obtener resultados de vuelo completos.
- Comparar el rendimiento de cada controlador neuronal frente al controlador clásico en cascada (PID + mixer) actual.
- Demostrar que al menos uno de los controladores neuronales iguala o supera al clásico en trayectorias exigentes y bajo perturbaciones.
- Generar evidencia cuantitativa y visual (gráficos y trayectorias en simulación) para justificar la selección en el TFG.

**Éxito de fase:** Las tres redes neuronales integradas y ejecutadas en el simulador, con resultados comparativos documentados y reproducibles.

## 2. Estrategia de Generación de Datos
- Utilizar el **controlador clásico existente** como “expert” para generar datos de demostración (Imitation Learning / Behavioral Cloning).
- Ejecutar múltiples trayectorias exigentes con diferentes perturbaciones: viento variable (constante + ráfagas), niveles de batería, saturación de actuadores.
- Loguear a 100-200 Hz:
  - Estado actual del dron (posición, velocidad lineal, Euler, velocidades angulares).
  - Referencia de trayectoria (posición/velocidad deseada, yaw deseado).
  - Acciones de control aplicadas por el controlador clásico.
- **Volumen objetivo**: mínimo 50-100 episodios de 60-120 s cada uno.
- **División train/val/test**: por trayectorias completas (time-series split).

*(Perturbaciones solo externas por ahora; ruido de sensores queda como opción abierta).*

## 3. Arquitecturas a probar
| Arquitectura | Rol                  | Ventajas esperadas                          | Desventajas                     |
|--------------|----------------------|---------------------------------------------|---------------------------------|
| **MLP**      | Baseline             | Simple, rápido de entrenar e inferir        | No captura memoria temporal     |
| **LSTM**     | Candidata principal  | Excelente para dependencias temporales      | Mayor coste computacional       |
| **GRU**      | Candidata eficiente  | Balance entre rendimiento y velocidad       | Ligeramente menor capacidad     |

**Input**: Estado actual + referencia de trayectoria (ventana temporal).  
**Output**: Comandos de control compatibles con el mixer existente (thrust total + momentos de torque o PWM por motor).  

*(Ampliación a Transformer ligero o TCN queda como extensión futura).*

## 4. Preparación y preprocesamiento de datos
- Ventanas temporales (sequence length): 10, 20, 50 pasos (a tunear).
- Normalización/estandarización por variable.
- División temporal estricta.
- Enfoque principal: **supervisado (Behavioral Cloning)**.

## 5. Proceso de entrenamiento y experimentación (PyTorch)
- Framework: PyTorch.
- Hiperparámetros clave a explorar según necesidad.
- Entrenamiento con early-stopping.

## 6. Criterios de evaluación y análisis comparativo

**Integración obligatoria con el simulador**:
- Cada red entrenada (MLP, LSTM y GRU) se carga y ejecuta **dentro del Runner** del simulador.
- Se realizan vuelos completos con las mismas trayectorias de test (nunca vistas en entrenamiento) y las mismas perturbaciones.
- Se comparan los resultados de las tres redes neuronales y del controlador clásico en el mismo entorno.

**Métricas principales (todas obligatorias):**
- **RMSE** y **MAE** de error de seguimiento (posición x,y,z y actitud).
- **R²** (Coefficient of Determination) y **correlación de Pearson** entre trayectoria deseada y real.
- Error de seguimiento integral (IAE / ISE).
- Suavidad de las señales de control (derivada de thrust y torques).
- Robustez a perturbaciones (viento más fuerte o no visto en entrenamiento).
- Tiempo de inferencia medio (ms por paso) en CPU.
- Estabilidad del vuelo (oscilaciones, overshoot, settling time).

**Presentación de resultados:**
- Tabla comparativa consolidada (clásico vs MLP vs LSTM vs GRU).
- Gráficos de trayectoria real vs deseada (vista 3D), evolución temporal de errores, señales de control.
- Análisis cualitativo de ventajas/desventajas observadas en simulación.

**Criterio de selección:** Mejor balance entre precisión de seguimiento, suavidad, robustez y velocidad de inferencia.

## 7. Hoja de ruta posterior a la fase
1. Documentar en el TFG los resultados de las tres redes integradas.
2. Seleccionar el mejor controlador neuronal para continuar.
3. Preparación para sim-to-real y posibles extensiones (MPC híbrido, RL fine-tuning, etc.).
4. Línea futura: optimización de trayectorias o control predictivo con el controlador seleccionado.

**Riesgos y mitigaciones:**
- Overfitting al comportamiento del controlador clásico → alta diversidad de trayectorias y perturbaciones.
- Inestabilidad en simulación → entrenamiento con ventanas temporales y posible regularización.
- Tiempo de inferencia elevado → priorizar GRU si es necesario.

## Checklist de tareas para completar Fase 2
- [ ] Generar dataset de demostraciones con controlador clásico.
- [ ] Entrenar MLP, LSTM y GRU.
- [ ] **Integrar cada red neuronal en el simulador** y ejecutar vuelos completos.
- [ ] Obtener y comparar resultados de las tres redes + controlador clásico.
- [ ] Documentar resultados (tablas, gráficos y análisis) en el informe.
- [ ] Actualizar documentación del proyecto (ADR + sección en memoria del TFG).
