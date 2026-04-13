# Backlog Técnico Recomendado

Fecha de corte: 2026-04-13 18:20

## Prioridad Alta

- Validar el modelo dinámico y aerodinámico con datos o referencias externas antes de usarlo para conclusiones cuantitativas fuertes.
- Añadir escenarios de referencia explícitos y versionados para comparativas repetibles entre PID y futuros controladores inteligentes.
- Incorporar carga/guardado de escenarios desde archivos `JSON` o `YAML` para dejar el flujo experimental menos acoplado al código.
- Definir una política clara de compatibilidad del esquema de exportación para no romper datasets ya generados.

## Prioridad Media

- Añadir controladores baseline alternativos además del cascaded PID para medir mejor el valor de la futura política inteligente.
- Introducir pruebas de integración más largas con trayectorias complejas y perturbaciones combinadas.
- Mejorar la salida de análisis con comparativas multi-run y artefactos listos para memoria del TFG.
- Registrar métricas adicionales relevantes para el TFG: sobreoscilación, error estacionario, coste acumulado y tiempos de asentamiento.

## Prioridad Media-Baja

- Ofrecer exportación vectorial o figuras configurables para documentación académica.
- Añadir análisis interactivo opcional en notebook sin acoplarlo al flujo principal.
- Refinar el modelo de viento para separar fondo, ráfagas y perfiles temporales más realistas.
- Preparar un adaptador específico para ingestión de datos reales del LiteWing.

## Riesgos De Evolución

- Cambiar contratos de telemetría sin migración romperá visualización, datasets y análisis acumulados.
- Endurecer demasiado pronto la física puede degradar mantenibilidad sin mejorar la utilidad experimental inmediata.
- Añadir dependencias grandes para visualización o configuración puede inflar el proyecto antes de necesitarlo de verdad.

## Criterio Práctico Para La Siguiente Iteración

La siguiente iteración debería priorizar aquello que mejore una de estas tres cosas:

1. confianza en la validez experimental del simulador
2. facilidad para comparar controladores
3. preparación real para datasets y transición sim-to-real
