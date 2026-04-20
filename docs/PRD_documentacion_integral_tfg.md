# PRD: Documentacion Integral Del TFG

## Problem Statement

El repositorio ya contiene documentacion relevante del TFG: PRDs por fase, ADRs de decisiones de arquitectura, documentos de estado, descripcion del dron fisico y notas metodologicas. Sin embargo, esa documentacion ha crecido alrededor de hitos concretos y no como un sistema documental unico. El resultado es que hoy existe informacion valiosa, pero repartida por fases, por temas y por niveles de abstraccion distintos, lo que dificulta usarla para explicar el proyecto de forma coherente ante tutores y para transformarla despues en capitulos de la memoria.

El problema no es solo mejorar la calidad de algunos documentos aislados, sino establecer una forma comun de documentar el TFG completo. Esa forma debe cubrir arquitectura, teoria fisico-matematica, ingenieria de sistemas y diseno software; debe conectar lo ya implementado con sus decisiones y simplificaciones; y debe dejar preparado un metodo estable para documentar el resto del trabajo sin rehacer el criterio en cada nueva entrega.

Desde la perspectiva del TFG, falta una vista simplificada de ingenieria de sistemas que permita responder de manera consistente a preguntas como: que subsistemas existen, como se relacionan, que interfaces los conectan, que teoria sustenta cada bloque, que decisiones justifican el diseno actual y como se traza todo eso hacia la memoria final.

## Solution

Se definira e implantara un sistema de documentacion integral para el TFG dentro de `docs/`, aprovechando la base ya existente y anadiendo una estructura documental comun. La solucion no sustituye las ADRs actuales, sino que las toma como mecanismo consolidado para decisiones de arquitectura y las conecta con nuevos documentos de contexto, teoria, sistema y software.

La documentacion objetivo se organizara en cuatro grandes vistas complementarias:

- vista de arquitectura y decisiones
- vista de teoria fisico-matematica
- vista de ingenieria de sistemas
- vista de diseno software

Cada vista tendra un proposito claro, una plantilla minima y un nivel de detalle acotado al alcance del TFG. La solucion debe documentar el sistema de forma explicable para el propio autor y para los tutores, sin caer en sobre-documentacion de bajo valor. En software se bajara hasta modulos, interfaces y clases principales; las funciones individuales no se documentaran de forma sistematica salvo que aporten valor excepcional.

El resultado esperado es doble:

1. mejorar y reorganizar la documentacion ya existente para que el estado actual del sistema quede claro
2. dejar definido un metodo estable para documentar el resto del TFG con coherencia y trazabilidad

Ademas, la estructura se dejara preparada para alimentar la memoria del TFG, manteniendo por ahora una relacion provisional entre documentos vivos del repositorio y futuros capitulos academicos.

## User Stories

1. Como autor del TFG, quiero una estructura unica de documentacion, para no explicar el proyecto de forma distinta en cada documento.
2. Como autor del TFG, quiero reorganizar la documentacion ya existente, para que el estado actual del sistema sea entendible sin reconstruir el contexto manualmente.
3. Como autor del TFG, quiero documentar la arquitectura y las decisiones principales, para justificar por que el sistema es como es.
4. Como autor del TFG, quiero mantener las ADRs como mecanismo oficial de decision, para no romper una convencion que ya funciona.
5. Como autor del TFG, quiero una vista simplificada de ingenieria de sistemas, para explicar el proyecto mediante capas, bloques e interfaces entre subsistemas.
6. Como autor del TFG, quiero documentar la teoria fisica y matematica que sustenta el simulador, para dejar clara la base teorica del trabajo.
7. Como autor del TFG, quiero separar la teoria del detalle de implementacion, para que cada documento responda a una pregunta distinta.
8. Como autor del TFG, quiero documentar subsistemas y sus fronteras, para explicar como se conectan dinamica, control, trayectorias, escenarios, telemetria, metricas y visualizacion.
9. Como autor del TFG, quiero documentar modulos, interfaces y clases principales, para poder explicar el diseno software a nivel adecuado para un TFG.
10. Como autor del TFG, quiero evitar documentar cada funcion individual, para concentrar el esfuerzo en los elementos estructurales del sistema.
11. Como tutor, quiero entender rapidamente el sistema completo, para evaluar el alcance y la coherencia del trabajo sin leer todo el codigo.
12. Como tutor, quiero ver que decisiones de arquitectura se conectan con las piezas implementadas, para poder revisar la consistencia tecnica del proyecto.
13. Como tutor, quiero ver que simplificaciones fisicas y matematicas se han adoptado, para evaluar si son validas para el alcance academico del TFG.
14. Como autor del TFG, quiero distinguir claramente entre documentacion de contexto, documentacion teorica y documentacion de implementacion, para no mezclar niveles de abstraccion.
15. Como autor del TFG, quiero plantillas simples para documentar nuevos elementos, para no improvisar el formato cada vez.
16. Como autor del TFG, quiero fichas de teoria, para resumir conceptos, ecuaciones, supuestos y su aplicacion dentro del sistema.
17. Como autor del TFG, quiero fichas de subsistemas fisicos, para describir elementos del dron y su papel en el modelo.
18. Como autor del TFG, quiero fichas de ingenieria de sistemas, para describir bloques, entradas, salidas, interfaces y responsabilidades.
19. Como autor del TFG, quiero fichas de modulos software, para describir responsabilidad, contratos, dependencias y clases principales.
20. Como autor del TFG, quiero fichas de interfaces y clases principales, para explicar las abstracciones relevantes del codigo.
21. Como autor del TFG, quiero una trazabilidad minima entre teoria, sistema, software y ADRs, para que las decisiones no queden aisladas.
22. Como autor del TFG, quiero vincular la documentacion viva con una estructura provisional de la memoria, para facilitar la redaccion posterior.
23. Como autor del TFG, quiero identificar documentos existentes que deben conservarse, consolidarse o reubicarse, para no duplicar contenido.
24. Como autor del TFG, quiero una portada o indice de documentacion del sistema, para que un lector nuevo sepa por donde empezar.
25. Como autor del TFG, quiero que la documentacion deje explicito que el proyecto es un TFG con alcance acotado, para justificar simplificaciones y prioridades.
26. Como autor del TFG, quiero que el marco documental sirva tanto para lo ya hecho como para futuras iteraciones, para no redisenar la estructura mas adelante.
27. Como tutor, quiero poder rastrear una decision desde una ADR hasta el modulo o subsistema que afecta, para entender impacto y justificacion.
28. Como autor del TFG, quiero que la documentacion del sistema no dependa de conocer todas las rutas internas del repositorio, para que siga siendo explicativa aunque evolucione el codigo.
29. Como autor del TFG, quiero una forma de documentar relaciones entre el dron fisico y el simulador, para dejar clara la frontera entre sistema real y modelo.
30. Como autor del TFG, quiero criterios de calidad documental, para decidir cuando una ficha esta suficientemente bien hecha.
31. Como autor del TFG, quiero que la documentacion sea reutilizable al preparar reuniones con tutores, para reducir trabajo de explicacion ad hoc.
32. Como autor del TFG, quiero que la estructura soporte el crecimiento del proyecto sin perder legibilidad, para mantener coherencia a medio plazo.

## Implementation Decisions

- Esta PRD define un sistema documental del repositorio, no una funcionalidad del simulador.
- La documentacion objetivo debe cubrir con el mismo peso arquitectura, teoria fisico-matematica, ingenieria de sistemas y diseno software.
- Las ADRs existentes se mantienen como fuente oficial de decisiones de arquitectura y no se sustituyen por una nueva plantilla.
- El nuevo sistema documental debe construirse alrededor de lo ya existente, priorizando reorganizacion y consolidacion antes que reescritura completa.
- La estructura de `docs/` debe reflejar vistas estables del sistema y no solo fases historicas del desarrollo.
- Se debe introducir una estructura documental explicita con secciones o carpetas para:
  - vision general
  - teoria
  - sistema
  - software
  - hardware o contexto fisico
  - decisiones
  - validacion o trazabilidad
  - plantillas
- Debe existir un documento de entrada principal que explique como navegar la documentacion y en que orden leerla.
- La vista de teoria debe documentar fundamentos fisicos y matematicos relevantes para el TFG, incluyendo supuestos, simplificaciones, magnitudes y relacion con el simulador.
- La vista de ingenieria de sistemas debe describir capas, bloques, interfaces entre subsistemas, entradas, salidas y responsabilidades.
- La vista de diseno software debe bajar hasta modulos, interfaces y clases principales; las funciones individuales quedan fuera del nivel documental por defecto.
- La documentacion del dron fisico debe mantenerse como contexto de sistema real y relacionarse con el modelo, pero sin forzar una equivalencia exacta entre hardware y simulacion.
- Debe introducirse trazabilidad explicita entre:
  - teoria y subsistemas
  - subsistemas y modulos software
  - modulos y ADRs aplicables
  - documentos vivos y capitulos provisionales de memoria
- Las referencias cruzadas deben ser ligeras y mantenibles; no se debe crear una matriz burocratica compleja.
- Las fichas nuevas deben ser breves, comparables entre si y centradas en responder preguntas estables.
- Cada ficha debe tener un identificador, proposito, alcance y relacion con otros documentos.
- Las plantillas nuevas a definir son:
  - ficha teorica
  - ficha de subsistema fisico
  - ficha de subsistema o bloque de sistema
  - ficha de modulo software
  - ficha de interfaz o clase principal
- La ficha teorica debe recoger concepto, formulacion esencial, supuestos, simplificaciones y donde aplica dentro del sistema.
- La ficha de subsistema fisico debe recoger funcion, elementos principales, limites del modelo y relacion con el dron real o con la plataforma objetivo.
- La ficha de sistema debe recoger responsabilidad, entradas, salidas, dependencias, interfaces y decisiones relacionadas.
- La ficha de modulo software debe recoger responsabilidad, contratos expuestos, clases principales, dependencias y extension points.
- La ficha de interfaz o clase principal debe recoger responsabilidad, colaboraciones, invariantes y papel dentro de la arquitectura.
- La documentacion debe reutilizar el lenguaje y contratos ya visibles en el codigo, como `VehicleState`, `VehicleObservation`, `VehicleCommand`, `TrajectoryReference` y `SimulationRunner`, para evitar desalineacion conceptual.
- La vista de sistema debe apoyarse en abstracciones ya estables del repositorio, especialmente los contratos de `core`, el `runner` y las fronteras entre `dynamics`, `control`, `trajectories`, `scenarios`, `telemetry`, `metrics`, `dataset`, `reporting` y `visualization`.
- Los documentos por fase ya existentes pueden seguir siendo utiles como historial o detalle especializado, pero la nueva estructura debe convertirse en la capa de lectura principal.
- La memoria del TFG se tratara como consumidor posterior de esta documentacion; los capitulos se reflejaran de forma provisional y podran renombrarse despues.

### Modulos o Areas Que Esta PRD Debe Cubrir

- Vision global del proyecto y su alcance academico.
- Fundamentos fisico-matematicos del simulador.
- Sistema objetivo y descomposicion en subsistemas.
- Contexto del dron fisico y frontera con el modelo de simulacion.
- Diseno software de los paquetes principales del repositorio.
- Contratos y abstracciones clave del nucleo.
- Trazabilidad entre decisiones, bloques y documentos.
- Relacion provisional entre documentacion viva y memoria del TFG.

### Estructura Documental Objetivo

- `docs/overview/`: contexto general, guia de navegacion y mapa de documentacion.
- `docs/theory/`: teoria fisica, matematica y supuestos.
- `docs/system/`: vistas de capas, bloques, interfaces y relaciones entre subsistemas.
- `docs/software/`: modulos, interfaces y clases principales.
- `docs/hardware/`: dron fisico, plataforma objetivo y frontera sim-to-real.
- `docs/decisions/`: ADRs existentes y futuras.
- `docs/validation/`: trazabilidad, limites, criterios de calidad documental y relacion con evidencias.
- `docs/templates/`: plantillas reutilizables para las nuevas fichas.

La estructura exacta puede adaptarse, pero estas vistas deben existir de forma reconocible y consistente.

### Propuesta De Fichas

- Ficha teorica: concepto, motivacion, formulacion esencial, supuestos, simplificaciones, impacto en el TFG y documentos relacionados.
- Ficha de subsistema fisico: proposito, elementos, variables relevantes, simplificaciones del modelo y relacion con el dron real.
- Ficha de subsistema de sistema: responsabilidad, entradas, salidas, interfaces, dependencias, decisiones relacionadas y riesgos o limites.
- Ficha de modulo software: responsabilidad, contratos, clases principales, dependencias, puntos de extension, pruebas relacionadas y ADRs asociadas.
- Ficha de interfaz o clase principal: rol arquitectonico, operaciones clave, invariantes, colaboradores y notas de uso.

## Testing Decisions

- Una buena validacion para esta PRD no consiste en tests automaticos del simulador, sino en verificar calidad, consistencia y utilidad de la documentacion generada.
- La documentacion debe validarse por comportamiento observable: que un lector pueda encontrar una respuesta concreta sin inspeccionar el codigo completo.
- Debe comprobarse que cada vista documental responde a una pregunta estable:
  - teoria: en que base fisica o matematica se apoya esto
  - sistema: que bloque hace que y como se conecta
  - software: donde vive la abstraccion y como se implementa
  - decisiones: por que se eligio asi
- Debe verificarse que no haya duplicacion innecesaria entre documentos; cuando un contenido tenga una fuente principal, el resto debe enlazarla en vez de repetirla.
- Debe verificarse que toda ficha nueva use una plantilla comun y mantenga un nivel de detalle comparable.
- Debe verificarse que las ADRs relevantes queden enlazadas desde los documentos de sistema o software cuando apliquen.
- Debe verificarse que los conceptos del codigo expuestos al lector coincidan con los contratos reales del repositorio.
- Debe verificarse que exista una trazabilidad minima hacia capitulos provisionales de la memoria.
- Debe verificarse que el sistema documental pueda ampliarse con nuevos bloques sin reorganizar por completo `docs/`.
- Como referencia de prior art interna, deben reutilizarse el tono y el nivel tecnico ya presentes en `estado_actual_simulador.md`, `extension-points.md`, `Dron_fisico.md` y las ADRs.

## Out of Scope

- Sustituir o reescribir todas las ADRs existentes.
- Documentar cada funcion individual del codigo.
- Convertir la documentacion del repo directamente en la memoria final del TFG.
- Definir una notacion formal pesada de ingenieria de sistemas mas alla de lo util para este trabajo.
- Crear una burocracia documental que obligue a mantener documentos de poco valor.
- Reestructurar el codigo fuente como parte de esta PRD.
- Resolver en esta PRD todos los huecos tecnicos del simulador o del dron fisico.
- Forzar una correspondencia exacta entre hardware real y modelo de simulacion.

## Further Notes

- El repositorio ya cuenta con una base suficiente para que esta PRD no empiece desde cero; el trabajo principal es convertir documentos dispersos en un sistema coherente.
- La nocion de "ingenieria de sistemas simplificada" debe materializarse en vistas legibles por capas, bloques e interfaces, no en formalismo academico excesivo.
- La documentacion debe servir para pensar, explicar y escribir la memoria, no solo para archivar informacion.
- La relacion con la memoria debe declararse como provisional para permitir ajustes posteriores de capitulos, nomenclatura y orden expositivo.
- El exito de esta PRD no se mide por cantidad de paginas, sino por claridad estructural, trazabilidad y facilidad de explicacion frente a tutores.
