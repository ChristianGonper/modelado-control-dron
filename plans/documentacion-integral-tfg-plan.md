# Plan: Documentacion Integral Del TFG

> Source PRD: [docs/PRD_documentacion_integral_tfg.md](../docs/PRD_documentacion_integral_tfg.md)

## Architectural decisions

Durable decisions that apply across all phases:

- **Documentation product boundary**: el alcance cubre la implantacion de un sistema documental del repositorio para el TFG, no una reescritura del simulador ni de sus ADRs existentes.
- **Primary audience**: la documentacion se optimiza principalmente para el propio autor del TFG y para los tutores que necesitan entender y revisar el sistema.
- **Documentation views**: la estructura oficial debe cubrir con el mismo peso arquitectura y decisiones, teoria fisico-matematica, ingenieria de sistemas y diseno software.
- **ADR policy**: las ADRs actuales se mantienen como mecanismo oficial de decision arquitectonica; el nuevo sistema documental debe enlazarlas, no sustituirlas.
- **System-engineering lens**: la vista de ingenieria de sistemas sera simplificada y se expresara mediante capas, bloques, interfaces entre subsistemas y trazabilidad de decisiones.
- **Software depth policy**: la documentacion software baja hasta modulos, interfaces y clases principales; la documentacion sistematica de funciones individuales queda fuera.
- **Structure policy**: la estructura objetivo de `docs/` debe reflejar vistas estables del sistema, no solo hitos o fases historicas del proyecto.
- **Reuse-before-rewrite policy**: la implantacion debe partir de la documentacion ya disponible en el repo, priorizando consolidacion, reubicacion y referencias cruzadas antes que rehacer contenido desde cero.
- **Traceability policy**: debe existir una trazabilidad ligera y mantenible entre teoria, sistema, software, contexto fisico, ADRs y capitulos provisionales de memoria.
- **Template policy**: las nuevas piezas documentales deben escribirse mediante fichas breves y comparables para teoria, subsistema fisico, bloque de sistema, modulo software e interfaz o clase principal.

---

## Phase 1: Mapa Documental Y Punto De Entrada

**User stories**: 1, 2, 11, 14, 23, 24, 25, 31, 32

### What to build

Construir el primer slice vertical del sistema documental: una capa principal de lectura que ordene la documentacion existente, explique el alcance academico del TFG y deje claro por donde debe empezar un lector nuevo. Esta fase debe convertir `docs/` en un espacio navegable, identificando que documentos actuales siguen siendo fuente principal, cuales pasan a ser contexto historico y como encajan dentro del nuevo mapa documental.

### Acceptance criteria

- [ ] Existe un documento de entrada principal que explica como leer la documentacion del TFG y en que orden hacerlo.
- [ ] La documentacion existente queda clasificada de forma explicita entre fuente principal, soporte especializado o historial.
- [ ] El mapa documental deja claro el alcance del TFG y las simplificaciones asumidas a nivel global.
- [ ] Un lector nuevo puede identificar rapidamente donde encontrar arquitectura, teoria, sistema, software y contexto fisico.
- [ ] La nueva capa de entrada reduce la dependencia de conocer la estructura interna del repositorio para entender el proyecto.

---

## Phase 2: Estructura Base Y Plantillas

**User stories**: 15, 16, 17, 18, 19, 20, 26, 30, 32

### What to build

Crear la base estable sobre la que crecera el resto del sistema documental: la estructura objetivo de `docs/` y el conjunto de plantillas reutilizables para documentar teoria, subsistema fisico, sistema, modulo software e interfaz o clase principal. Esta fase debe dejar el marco listo para que el contenido tecnico posterior se escriba con formato consistente y sin improvisacion.

### Acceptance criteria

- [ ] La estructura objetivo de `docs/` existe de forma reconocible para overview, theory, system, software, hardware, decisions, validation y templates.
- [ ] Existen plantillas reutilizables para ficha teorica, subsistema fisico, bloque de sistema, modulo software e interfaz o clase principal.
- [ ] Todas las plantillas comparten un nivel de detalle comparable y responden a preguntas estables.
- [ ] Las plantillas dejan espacio para enlazar ADRs, documentos relacionados y trazabilidad hacia memoria.
- [ ] El sistema documental puede crecer con nuevos documentos sin tener que redefinir carpetas ni formatos base.

---

## Phase 3: Vista De Sistema Por Capas Y Bloques

**User stories**: 3, 5, 8, 11, 18, 25, 28, 29

### What to build

Implantar la primera vista tecnica end-to-end de ingenieria de sistemas simplificada, centrada en capas, bloques funcionales y responsabilidades del sistema. Esta fase debe explicar como se descompone el proyecto en subsistemas y como se relacionan dinamica, control, trayectorias, escenarios, telemetria, metricas, reporting, dataset y visualizacion, sin entrar todavia en el detalle fino de cada interfaz o decision enlazada.

### Acceptance criteria

- [ ] Existe una vista de sistema que describe las capas y bloques principales del proyecto con lenguaje estable y entendible para tutores.
- [ ] Cada bloque documentado deja clara su responsabilidad y su papel dentro del sistema completo.
- [ ] La vista de sistema conecta el simulador con el contexto fisico del dron sin forzar equivalencia exacta entre ambos.
- [ ] El lector puede entender el flujo principal del sistema sin inspeccionar directamente el codigo.
- [ ] La descomposicion de subsistemas es compatible con la estructura real y las abstracciones actuales del repositorio.

---

## Phase 4: Interfaces Entre Subsistemas Y Trazabilidad Con ADRs

**User stories**: 4, 12, 18, 21, 27, 28, 29

### What to build

Extender la vista de sistema anterior con la documentacion de interfaces entre subsistemas y la trazabilidad minima hacia decisiones de arquitectura. Esta fase debe mostrar como se conectan los bloques entre si, que contratos conceptuales atraviesan el sistema y que ADRs justifican las fronteras principales, manteniendo una trazabilidad ligera y mantenible.

### Acceptance criteria

- [ ] Las interfaces principales entre subsistemas estan documentadas con sus entradas, salidas y responsabilidades.
- [ ] La documentacion reutiliza las abstracciones y contratos estables ya visibles en el codigo y en las ADRs existentes.
- [ ] Cada bloque o interfaz relevante enlaza las ADRs que justifican su forma actual cuando aplique.
- [ ] La trazabilidad entre sistema y decisiones es suficiente para seguir una justificacion tecnica sin crear burocracia excesiva.
- [ ] Un tutor puede rastrear una decision desde su ADR hasta el bloque o contrato del sistema afectado.

---

## Phase 5: Base Teorico-Fisico-Matematica

**User stories**: 6, 7, 13, 16, 17, 21, 25, 29

### What to build

Construir la vista teorica del TFG mediante fichas estructuradas que documenten los fundamentos fisicos y matematicos relevantes, las simplificaciones del modelo y su relacion con el sistema implementado. Esta fase debe separar con claridad teoria, contexto fisico y decisiones de modelado, conectando cada concepto con su aplicacion dentro del simulador y con los limites del alcance academico.

### Acceptance criteria

- [ ] Existen fichas teoricas para los conceptos fisicos y matematicos principales que sostienen el simulador.
- [ ] Las simplificaciones y supuestos del modelo quedan documentados de forma explicita y revisable.
- [ ] La relacion entre teoria, sistema y contexto fisico del dron queda clara sin mezclar niveles de abstraccion.
- [ ] Cada ficha teorica indica donde aplica dentro del sistema y con que otras piezas se relaciona.
- [ ] La vista teorica sirve como base reutilizable para reuniones con tutores y para futuros capitulos de memoria.

---

## Phase 6: Diseno Software Y Abstracciones Principales

**User stories**: 9, 10, 19, 20, 21, 27, 28

### What to build

Documentar el diseno software del proyecto con el nivel adecuado para el TFG, cubriendo paquetes principales, contratos compartidos, modulos relevantes y clases principales. Esta fase debe explicar donde viven las abstracciones del sistema, como colaboran entre si y que extension points o fronteras de diseno son importantes, evitando caer en documentacion exhaustiva de funciones.

### Acceptance criteria

- [ ] Los paquetes y modulos principales del repositorio cuentan con fichas software coherentes con la arquitectura documentada.
- [ ] Las interfaces y clases principales quedan descritas con su rol, colaboraciones e invariantes relevantes.
- [ ] La documentacion software se mantiene alineada con los contratos reales del proyecto y con la terminologia usada en el codigo.
- [ ] Los puntos de extension importantes quedan documentados sin duplicar innecesariamente contenido ya existente.
- [ ] Un lector tecnico puede explicar el diseno software del TFG sin necesidad de recorrer todos los archivos fuente.

---

## Phase 7: Memoria Provisional, Validacion Y Cierre

**User stories**: 22, 30, 31, 32

### What to build

Cerrar el sistema documental con una capa de validacion y trazabilidad hacia la memoria del TFG. Esta fase debe dejar claros los criterios de calidad documental, la relacion provisional entre documentos vivos y capitulos de memoria, y una revision final de consistencia para asegurar que el sistema completo se puede mantener y reutilizar sin redescubrir su logica organizativa.

### Acceptance criteria

- [ ] Existe una relacion provisional y explicita entre la documentacion viva del repositorio y futuros capitulos de la memoria.
- [ ] Hay criterios de calidad documental que permitan decidir cuando una ficha o vista esta suficientemente completa.
- [ ] La revision final confirma coherencia entre overview, teoria, sistema, software, hardware y ADRs.
- [ ] El sistema documental queda listo para crecer con nuevas iteraciones sin perder legibilidad ni estructura.
- [ ] La documentacion final es util tanto para redactar la memoria como para preparar explicaciones tecnicas frente a tutores.
