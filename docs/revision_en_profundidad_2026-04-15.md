# Revisión en profundidad del proyecto (2026-04-15)

## 1) Resumen ejecutivo

El proyecto muestra una madurez técnica alta para un simulador académico modular orientado a control de multirrotor: contratos consistentes, separación limpia por capas, trazabilidad de decisiones mediante ADRs y una batería de tests extensa (78 tests pasando). La base es sólida para experimentación reproducible y para comparar control clásico vs aproximadores neuronales (MLP, GRU, LSTM).

A la vez, la fidelidad física sigue siendo intencionadamente compacta (coherente con el alcance), por lo que no debería usarse para conclusiones fuertes de performance absoluta sin validación externa. En redes neuronales, la base de entrenamiento y benchmark está bien estructurada, pero aún falta cerrar del todo la validez externa (generalización temporal, OOD y sim-to-real). Las mejoras prioritarias para la siguiente iteración deberían centrarse en: (i) calibración/validación del modelo físico, (ii) robustez numérica y de saturación del mixer, (iii) endurecimiento de la documentación de limitaciones y supuestos para evitar sobre-interpretación y (iv) madurez metodológica del pipeline de ML.

## 2) Fortalezas identificadas

### 2.1 Arquitectura e implementación de alto nivel

1. **Diseño modular claro y extensible.**
   - Separación explícita entre `core`, `dynamics`, `control`, `scenarios`, `telemetry`, `metrics`, `visualization` y `runner`.
   - Esto reduce acoplamiento y facilita evolución incremental por fases.

2. **Contrato de escenarios robusto.**
   - Validación estricta de tipos, campos requeridos y rechazo de claves desconocidas.
   - Reglas de coherencia temporal (`control_dt_s` y `telemetry_dt_s` múltiplos de `physics_dt_s`) bien definidas.

3. **Runner bien instrumentado para experimentación.**
   - Mantiene separación entre estado real y observado.
   - Emite eventos de telemetría útiles (`simulation_start`, `trajectory_exhausted`, `simulation_complete`) y metadatos de perturbaciones.

4. **Pipeline de medición bien encaminado.**
   - Métricas de seguimiento con RMSE/MAE/IAE/ISE, variación de mando y comparador homogéneo.
   - Buen equilibrio entre métricas de tracking y métricas de esfuerzo/suavidad de control.

### 2.2 Física / ingeniería

1. **Dinámica 6DOF razonable para “tracer bullet”.**
   - Integración RK4 para variables traslacionales/rotacionales.
   - Propagación de actitud con cuaterniones y normalización para estabilidad geométrica.

2. **Modelo de actuadores y mixer con valor práctico.**
   - Dinámica de motor de primer orden con constante de tiempo.
   - Asignación de esfuerzos mediante sistema sobredeterminado (`lstsq`) y límites por rotor.

3. **Perturbaciones reproducibles y separables.**
   - Viento base + ráfaga estocástica OU con semilla reproducible.
   - Drag parasitario e inducido activables por escenario, lo que permite análisis controlados por componentes.

### 2.3 Documentación y gobernanza técnica

1. **Uso sistemático de ADRs.**
   - Las decisiones clave están justificadas y fechadas.

2. **Backlog técnico honesto y útil.**
   - Reconoce límites actuales, riesgos de evolución y prioridades realistas.

3. **Estado actual y PRDs facilitan onboarding.**
   - Se entiende rápidamente qué está entregado y qué no.

### 2.4 Redes neuronales y pipeline de ML

1. **Pipeline reproducible de entrenamiento por fases (MLP → GRU/LSTM).**
   - Configuración explícita de seeds para entrenamiento y split.
   - Persistencia de checkpoints auditables con metadatos de entrenamiento, normalización, features y targets.

2. **Normalización correcta usando solo train split.**
   - Se evita fuga de información desde validación/test.
   - Este punto está reforzado por tests específicos.

3. **Comparación homogénea entre baseline y modelos neuronales.**
   - Benchmark común para `baseline`, `mlp`, `gru` y `lstm`.
   - Inclusión de coste de inferencia CPU junto con métricas de tracking/suavidad/robustez.

4. **Separación metodológica ID vs OOD ya planteada.**
   - El proyecto distingue claramente benchmark principal y batería OOD, reduciendo riesgo de “selección por test set”.

## 3) Puntos a mejorar (priorizados)

## P0 — Crítico antes de “conclusiones cuantitativas fuertes”

1. **Falta validación contra referencia externa (datos o benchmark físico).**
   - Riesgo: extrapolar resultados de control más allá de la validez del modelo.
   - Recomendación: campaña mínima de identificación/calibración (masa efectiva, inercia, empuje vs velocidad de rotor, drag equivalente) y pruebas de regresión comparando simulación vs referencias.

2. **Modelo aerodinámico agregado con límites conocidos.**
   - Es correcto para fase inicial, pero no captura acoplamientos rotor-estructura ni fenómenos más ricos (transitorios inducidos, no linealidades por ángulo de ataque).
   - Recomendación: introducir una “capa intermedia” con coeficientes identificables por eje y opcionalmente términos cruzados, sin saltar aún a blade-element completo.

## P1 — Alto impacto técnico

3. **Asignación por `lstsq` + recorte por rotor puede romper la consistencia de wrench objetivo.**
   - Al saturar cada rotor post-solución, el wrench final puede desviarse de forma no óptima.
   - Recomendación: allocator con restricciones (QP/least-squares con bounds) o realocación iterativa con prioridad (empuje total vs yaw, etc.).

4. **Control cascada sin anti-windup ni scheduling explícito de ganancias.**
   - Actualmente no hay integrador en lazo de posición/actitud (reduce riesgo de windup), pero tampoco compensación sistemática de sesgos sostenidos.
   - Recomendación: añadir término integral opcional con anti-windup y plantillas de tuning por régimen (hover/traslación/agresivo).

5. **Gestión de incertidumbre y ruido: bien iniciada, aún parcial.**
   - Hay perturbación de observación, pero faltan modelos más ricos de sensores (bias lento, escalado, desalineación) para ensayos de estimación/control más realistas.
   - Recomendación: módulo de “sensor faults/noise profiles” versionado en escenarios.

6. **Riesgo de sobreajuste por cobertura limitada del dataset de demostraciones.**
   - El enfoque actual (imitation learning) depende de la diversidad/calidad de episodios del controlador experto.
   - Recomendación: ampliar la cobertura del dataset (más trayectorias, perturbaciones y seeds) y reportar métricas por subgrupo de escenarios.

7. **Capacidad de los modelos vs horizonte temporal: criterio aún rígido.**
   - Ventanas fijas por arquitectura (MLP/GRU/LSTM) ayudan a trazabilidad, pero conviene validar sensibilidad a ventana, stride y tamaño de red.
   - Recomendación: barrido sistemático de hiperparámetros con presupuesto fijo y reporte de varianza por seed.

## P2 — Mejora de calidad de producto y mantenibilidad

6. **Documentación técnica: reforzar matriz “supuesto → impacto”.**
   - El repositorio ya advierte límites, pero convendría una tabla única y visible de: simplificación, impacto esperado y cuándo deja de ser válida.

7. **Trazabilidad de unidades y convenciones.**
   - Hay buen naming en SI, pero sería valioso un documento canónico de marcos de referencia (world/body), signos, yaw convention y criterios de validación numérica.

8. **Estrategia de compatibilidad de artefactos.**
   - Ya se menciona en backlog; conviene formalizar versión semántica de contratos de telemetría/dataset y política de migración.

9. **Métricas de ML orientadas a control: completar panel de diagnóstico.**
   - Hoy hay un conjunto útil de métricas de tracking y suavidad; faltan curvas de aprendizaje agregadas, calibración por escenario y análisis de fallos por región operativa.
   - Recomendación: añadir reporte de “failure cases” (top-N episodios peores) y dispersión entre seeds.

## 4) Hallazgos por dimensión

### 4.1 Física e ingeniería

- **Lo positivo:** base dinámica coherente, perturbaciones desacopladas y reproducibles, y mezcla rotor/actuador adecuada para etapa académica.
- **Riesgo principal:** la distancia entre “plausible” y “predictivo” aún es significativa.
- **Siguiente paso recomendado:** validación cuantitativa en 3 maniobras canónicas (hover, escalón vertical, traslación lateral) con umbrales de error aceptables por magnitud medida.

### 4.2 Implementación de alto nivel

- **Lo positivo:** arquitectura limpia, contratos explícitos, separaciones correctas de responsabilidades, pruebas extensas.
- **Riesgo principal:** allocator y saturaciones bajo maniobras exigentes; potencial gap entre intención de control y acción física efectiva.
- **Siguiente paso recomendado:** introducir tests de estrés de saturación/maniobra combinada y reportar degradación de tracking + esfuerzo de mando.

### 4.3 Documentación

- **Lo positivo:** documentación abundante y alineada con evolución por fases.
- **Riesgo principal:** dispersión de información crítica en múltiples documentos y posibilidad de interpretación optimista por lectores nuevos.
- **Siguiente paso recomendado:** “Guía de validez del simulador” (1 página) en `README`/`docs` con semáforo de usos permitidos/no permitidos.

### 4.4 Redes neuronales

- **Lo positivo:** pipeline bien definido para entrenamiento, checkpointing, carga en inferencia y benchmark unificado entre modelos.
- **Riesgo principal:** la robustez observada puede depender demasiado de una distribución de entrenamiento todavía estrecha y del experto que se imita.
- **Siguiente paso recomendado:** validar generalización en splits temporales y de escenarios no vistos, con intervalos de confianza por seed y reporte explícito de degradación OOD frente a ID.

## 5) Propuesta de roadmap (8-10 semanas)

### Sprint A (semanas 1-2): Validación mínima de física
- Definir 3 escenarios de validación y métricas objetivo.
- Calibrar 3-5 parámetros efectivos (empuje, drag, pérdidas inducidas).
- Añadir reporte automático de error sim vs referencia.

### Sprint B (semanas 3-4): Robustez de control y asignación
- Implementar allocator acotado (con límites) y comparar frente al actual.
- Añadir suite de estrés (saturación, viento fuerte, cambios de trayectoria bruscos).

### Sprint C (semanas 5-6): Madurez de redes neuronales
- Ampliar dataset de demostraciones (trayectorias, disturbios, seeds) y medir cobertura.
- Ejecutar barrido acotado de hiperparámetros y reportar varianza por seed.
- Añadir informe de fallos (escenarios de peor rendimiento) para MLP/GRU/LSTM.

### Sprint D (semanas 7-8): Documentación de validez + contratos
- Publicar matriz de supuestos y dominios de validez.
- Congelar versión de esquemas de telemetría/dataset y política de migración.

### Sprint E (semanas 9-10): Cierre experimental
- Ejecutar benchmark homogéneo completo con trazabilidad de configuración.
- Consolidar conclusiones: qué afirmaciones son robustas y cuáles exploratorias.

## 6) Conclusión

El proyecto está **muy bien encaminado**: arquitectura cuidada, reproducibilidad, testeo y documentación por encima de la media para un simulador de esta etapa. El principal salto de calidad ya no está en “más features”, sino en **cerrar el ciclo de validez física y robustez bajo saturación/perturbaciones**. Si se ejecuta el roadmap propuesto, el trabajo puede pasar de una plataforma experimental sólida a una base técnica defendible para conclusiones más exigentes.
