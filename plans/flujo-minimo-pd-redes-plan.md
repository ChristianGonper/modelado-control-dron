# Plan: Flujo Minimo Repetible Desde PD Hasta Redes

> Source PRD: [docs/PRD_flujo_minimo_pd_redes.md](../docs/PRD_flujo_minimo_pd_redes.md)

## Architectural decisions

Durable decisions that apply across all phases:

- **Vehicle baseline**: el flujo se apoya en un unico perfil de "dron generico de referencia", modelado como cuadricoptero `X` con parametros fisicos y de actuadores explicitamente documentados.
- **Scenario contract**: la configuracion oficial sigue viviendo en el contrato de escenarios existente; masa, inercias, limites, tiempos, trayectoria y ganancias deben seguir siendo configurables desde ahi o desde artefactos equivalentes trazables.
- **Expert policy boundary**: la politica experta de referencia para generar datos sigue siendo el controlador en cascada actual de tipo PD/PD-like; no se introduce otro experto en este plan.
- **Validation gate**: ninguna telemetria podra considerarse fuente oficial de entrenamiento sin pasar antes por una validacion explicita del baseline PD.
- **Training source of truth**: dataset y entrenamiento siguen construyendose exclusivamente desde telemetria persistida exportada por el simulador.
- **Observability policy**: el control usa `observed_state` y la evaluacion usa `true_state`; esta convencion debe mantenerse visible en artefactos, CLI y documentacion.
- **Architecture scope**: el flujo neuronal oficial cubre exactamente `MLP`, `GRU` y `LSTM`.
- **Artifact policy**: el flujo debe dejar artefactos separados y encadenables para baseline, telemetria fuente, dataset, checkpoints, benchmark principal, benchmark OOD y reporte final.
- **Reproducibility policy**: cada fase debe persistir configuracion efectiva, seeds y origenes de datos suficientes para repetir el experimento modificando parametros declarados.
- **Methodology boundary**: benchmark principal y OOD siguen siendo flujos separados; OOD no participa en seleccion ni tuning.

---

## Phase 1: Baseline Del Dron Generico

**User stories**: 1, 2, 3, 4, 5, 10, 11, 12, 25, 26, 28, 30

### What to build

Definir y documentar un perfil baseline unico de dron generico, con parametros fisicos, de actuadores y de control suficientemente claros como para servir de base experimental reproducible. Esta fase debe cerrar el "que dron estoy simulando" antes de entrar en validacion de trayectorias o entrenamiento.

### Acceptance criteria

- [ ] Existe un perfil baseline unico y reconocible para el dron generico de referencia.
- [ ] Los parametros del baseline quedan documentados con unidades, significado y rol dentro del simulador.
- [ ] La documentacion separa claramente parametros fisicos, parametros del controlador y parametros del experimento.
- [ ] La configuracion baseline puede reutilizarse y modificarse sin romper el contrato general de escenarios.
- [ ] Un lector tecnico puede entender que supuestos son genericamente defendibles y cuales limitan la validez externa.

---

## Phase 2: Validacion PD Sobre Trayectoria Minima

**User stories**: 6, 7, 8, 9, 10, 12, 13, 14, 21, 24, 29, 30

### What to build

Construir el primer slice validable del flujo: una trayectoria minima y unos criterios de aceptacion observables que permitan decidir si el baseline PD es suficientemente estable para producir telemetria experta. Esta fase debe dejar un recorrido corto y demostrable de simulacion baseline con salida trazable.

### Acceptance criteria

- [ ] Existe al menos un escenario minimo de validacion PD asociado al baseline del dron generico.
- [ ] La trayectoria minima y los criterios de aceptacion quedan explicitamente definidos y documentados.
- [ ] La validacion PD produce una salida observable que permite decidir si la baseline es apta para generar dataset.
- [ ] La telemetria baseline exportada conserva metadata suficiente de escenario, controlador y referencia.
- [ ] Un usuario puede ejecutar esta validacion como primer recorrido minimo del proyecto.

---

## Phase 3: Bateria Minima De Telemetria Experta

**User stories**: 8, 9, 13, 14, 15, 16, 17, 18, 21, 24, 25, 27, 30

### What to build

Extender la validacion minima hacia una bateria pequena y repetible de trayectorias nativas que sirva para generar telemetria experta util para entrenamiento. Esta fase debe cerrar el puente entre baseline PD validado y artefactos fuente del pipeline neuronal.

### Acceptance criteria

- [ ] Existe una bateria minima de trayectorias fuente documentada y separada del escenario de validacion PD.
- [ ] La bateria produce telemetrias persistidas reutilizables como fuente oficial de dataset.
- [ ] Cada telemetria conserva suficiente trazabilidad para reconstruir dron baseline, trayectoria, ganancias y seed.
- [ ] La documentacion explica cuando una bateria modificada sigue siendo comparable y cuando abre una nueva campaña experimental.
- [ ] El flujo deja claro que la telemetria fuente proviene del experto PD ya validado.

---

## Phase 4: Dataset Operable Y Trazable

**User stories**: 17, 18, 21, 24, 25, 26, 27, 29, 30

### What to build

Construir el slice completo que convierte telemetria experta persistida en un dataset reproducible y auditable. Esta fase debe dejar un artefacto intermedio bien definido que cierre la parte previa al entrenamiento neuronal.

### Acceptance criteria

- [ ] Existe un flujo operable que toma telemetria persistida y genera un dataset listo para entrenamiento.
- [ ] El dataset registra seeds, feature mode, split y procedencia de episodios.
- [ ] Los artefactos de dataset quedan claramente separados de baseline, checkpoints y reportes.
- [ ] La salida permite reconstruir que telemetrias y parametros produjeron el dataset.
- [ ] Un recorrido minimo puede detenerse aqui y dejar un dataset reutilizable por fases posteriores.

---

## Phase 5: Entrenamiento Neuronal E Inspeccion

**User stories**: 19, 20, 21, 24, 25, 26, 27, 29, 30

### What to build

Construir el slice de entrenamiento e inspeccion para `MLP`, `GRU` y `LSTM`, reutilizando el pipeline ya existente pero dejandolo integrado como parte del flujo minimo reproducible. Esta fase debe producir checkpoints legibles, auditables y comparables.

### Acceptance criteria

- [ ] Existe un flujo operable para entrenar `MLP`, `GRU` y `LSTM` sobre el dataset oficial.
- [ ] Cada entrenamiento deja checkpoint, configuracion efectiva y resumen legible para auditoria.
- [ ] Existe una forma operable de inspeccionar un checkpoint y reconstruir sus parametros relevantes.
- [ ] El entrenamiento conserva la trazabilidad con el baseline PD y la telemetria fuente que originaron el dataset.
- [ ] Un usuario puede repetir el entrenamiento modificando hiperparametros o seeds sin perder el contrato general del flujo.

---

## Phase 6: Benchmark Final, OOD Y Reporte

**User stories**: 21, 22, 23, 24, 25, 28, 29, 30

### What to build

Cerrar el flujo extremo a extremo comparando las redes frente al baseline PD, separando benchmark principal y OOD, y generando un reporte final reutilizable para el TFG. Esta fase convierte el pipeline en un resultado experimental completo y documentado.

### Acceptance criteria

- [ ] Existe un benchmark principal reproducible frente al baseline PD para `MLP`, `GRU` y `LSTM`.
- [ ] Existe una ruta separada para benchmark OOD que no se usa para seleccion ni tuning.
- [ ] El reporte final incluye tabla, seleccion, figuras y una explicacion metodologica legible.
- [ ] Los artefactos finales permiten reconstruir la cadena baseline -> telemetria -> dataset -> checkpoint -> benchmark -> reporte.
- [ ] Un tutor o revisor puede seguir la guia operativa y entender el flujo completo sin deducirlo desde el codigo fuente.
