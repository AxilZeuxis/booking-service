# Notas sobre uso de IA

## Qué partes hice con ayuda de IA

- Lectura y extracción de los requisitos desde el PDF.
- Propuesta inicial de estructura del proyecto.
- Generación de una primera versión de modelos, reglas, endpoints y pruebas.
- Redacción inicial del README y de esta nota de transparencia.

## Qué partes ajusté o decidí manualmente

- Tomé el PDF como fuente principal y traté `PROYECTO.md` solo como ideas preliminares.
- Agregué `price_cents` al catálogo de servicios porque el PDF pide calcular monto a cobrar o reembolsar, no solo porcentaje.
- Definí los bordes exactos de reembolso en 24h, 4h y 1h para evitar ambigüedades.
- Separé la lógica de negocio en `app/rules.py` para que sea fácil de probar y explicar.
- Elegí persistencia JSON en lugar de base de datos para mantener el alcance razonable.

## Por qué hice esos ajustes

La prueba evalúa correctitud, casos borde, claridad, documentación y calidad de pruebas. Por eso prioricé una solución simple, defendible y con reglas explícitas sobre una arquitectura más sofisticada.

## Uso responsable

La IA ayudó a acelerar el desarrollo, pero las decisiones de alcance, supuestos y trade-offs quedaron documentadas para poder defenderlas en entrevista.

