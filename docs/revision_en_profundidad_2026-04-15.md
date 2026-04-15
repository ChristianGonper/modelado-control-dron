# Revisión en profundidad del proyecto (2026-04-15)

## 1) Resumen ejecutivo

El proyecto muestra una madurez técnica alta para un simulador académico modular orientado a control de multirrotor: contratos consistentes, separación limpia por capas, trazabilidad de decisiones mediante ADRs y una batería de tests extensa (78 tests pasando). La base es sólida para experimentación reproducible y para comparar control clásico vs aproximadores neuronales.

A la vez, la fidelidad física sigue siendo intencionadamente compacta (coherente con el alcance), por lo que no debería usarse para conclusiones fuertes de performance absoluta sin validación externa. Las mejoras prioritarias para la siguiente iteración deberían centrarse en: (i) calibración/validación del modelo físico, (ii) robustez numérica y de saturación del mixer, y (iii) endurecimiento de la documentación de limitaciones y supuestos para evitar sobre-interpretación.

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

## P2 — Mejora de calidad de producto y mantenibilidad

6. **Documentación técnica: reforzar matriz “supuesto → impacto”.**
   - El repositorio ya advierte límites, pero convendría una tabla única y visible de: simplificación, impacto esperado y cuándo deja de ser válida.

7. **Trazabilidad de unidades y convenciones.**
   - Hay buen naming en SI, pero sería valioso un documento canónico de marcos de referencia (world/body), signos, yaw convention y criterios de validación numérica.

8. **Estrategia de compatibilidad de artefactos.**
   - Ya se menciona en backlog; conviene formalizar versión semántica de contratos de telemetría/dataset y política de migración.

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

## 5) Propuesta de roadmap (6-8 semanas)

### Sprint A (semanas 1-2): Validación mínima de física
- Definir 3 escenarios de validación y métricas objetivo.
- Calibrar 3-5 parámetros efectivos (empuje, drag, pérdidas inducidas).
- Añadir reporte automático de error sim vs referencia.

### Sprint B (semanas 3-4): Robustez de control y asignación
- Implementar allocator acotado (con límites) y comparar frente al actual.
- Añadir suite de estrés (saturación, viento fuerte, cambios de trayectoria bruscos).

### Sprint C (semanas 5-6): Documentación de validez + contratos
- Publicar matriz de supuestos y dominios de validez.
- Congelar versión de esquemas de telemetría/dataset y política de migración.

### Sprint D (semanas 7-8): Cierre experimental
- Ejecutar benchmark homogéneo completo con trazabilidad de configuración.
- Consolidar conclusiones: qué afirmaciones son robustas y cuáles exploratorias.

## 6) Conclusión

El proyecto está **muy bien encaminado**: arquitectura cuidada, reproducibilidad, testeo y documentación por encima de la media para un simulador de esta etapa. El principal salto de calidad ya no está en “más features”, sino en **cerrar el ciclo de validez física y robustez bajo saturación/perturbaciones**. Si se ejecuta el roadmap propuesto, el trabajo puede pasar de una plataforma experimental sólida a una base técnica defendible para conclusiones más exigentes.
