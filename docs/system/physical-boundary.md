# Frontera física y contexto del dron

## Propósito

Este documento aclara cómo se relaciona el dron físico de referencia con el
sistema descrito en el TFG y dónde está la frontera entre realidad, modelo y
alcance académico.

## Tres niveles que conviene separar

### 1. Sistema real

Es el dron físico y su ecosistema operativo: estructura, motores, batería,
sensores, firmware embebido, comunicaciones y condiciones reales de vuelo.

En la documentación actual, esta referencia aparece sobre todo en
[Dron Físico](/Users/chris/Documents/Universidad/TFG/docs/Dron_fisico.md).

### 2. Sistema modelado

Es el simulador implementado en este repositorio. Representa solo la parte del
problema que el TFG necesita para experimentar con seguimiento de trayectorias,
telemetría, métricas y control neuronal reproducible.

Incluye:

- estado y observación del vehículo
- dinámica rígida simplificada y entorno aerodinámico compacto
- trayectorias, perturbaciones y escenarios
- control baseline y controladores neuronales
- telemetría, análisis, benchmark y reporting

### 3. Alcance del TFG

Es la porción del sistema modelado que se justifica como trabajo académico
actual. El foco no es construir un gemelo digital completo ni desplegar un
stack de vuelo en hardware, sino una plataforma experimental trazable.

## Cómo informa el dron físico al sistema

El dron físico informa el sistema en varios niveles:

- dominio del problema: se trabaja sobre un multirrotor realista, no sobre un
  agente abstracto cualquiera
- magnitudes y componentes: masa, empuje, sensores, perturbaciones y referencias
  se entienden desde un contexto de dron real
- interpretación de resultados: el análisis se discute con cautela respecto a
  posibles implicaciones sim-to-real
- límites metodológicos: se recuerda qué aspectos del hardware, firmware y
  operación real no quedan representados

## Qué no debe inferirse

Esta documentación no afirma que:

- cada parámetro del simulador corresponda uno a uno con el LiteWing real
- la dinámica implementada reproduzca con fidelidad completa el dron físico
- un resultado bueno en simulación garantice rendimiento equivalente en vuelo real
- el controlador neuronal entrenado aquí sea directamente desplegable sin una
  fase adicional de validación y adaptación

## Mapeo cualitativo entre contexto físico y sistema modelado

| Contexto físico | En el sistema modelado | Tipo de relación |
| --- | --- | --- |
| Multirrotor, masa, inercias, empuje | `vehicle` y `dynamics/` | Abstracción física simplificada |
| Trayectoria deseada y maniobra | `trajectories/` y `scenarios/` | Representación experimental |
| Sensado imperfecto | `VehicleObservation` y ruido de observación | Aproximación controlada |
| Perturbaciones ambientales | bloque `disturbances` y aerodinámica | Modelo parcial |
| Acción de control | `ControllerContract` y `VehicleCommand` | Frontera funcional |
| Registro de vuelo | `telemetry/` | Trazabilidad del experimento modelado |

## Frontera práctica para explicar el TFG

Una forma breve de contarlo es:

"El dron físico define el contexto y orienta el modelo, pero el sistema que se
ejecuta en el TFG es un simulador académico con simplificaciones explícitas.
Ese simulador permite comparar control clásico y control neuronal de forma
reproducible sin afirmar todavía equivalencia fuerte con el vuelo real."

## Enlaces relacionados

- [Vista de sistema por capas](/Users/chris/Documents/Universidad/TFG/docs/system/layered-system-view.md)
- [Bloques y responsabilidades principales](/Users/chris/Documents/Universidad/TFG/docs/system/system-blocks.md)
- [Hardware README](/Users/chris/Documents/Universidad/TFG/docs/hardware/README.md)
- [Dron Físico](/Users/chris/Documents/Universidad/TFG/docs/Dron_fisico.md)
