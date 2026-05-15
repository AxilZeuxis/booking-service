# Notas sobre uso de IA

## Enfoque general

Aborde esta prueba como lo haría con cualquier proyecto técnico en mi trabajo actual: usando IA de forma intensiva como herramienta de productividad, dirigiendo el proceso con criterio de arquitecto en lugar de programar línea por línea. La prueba pide transparencia sobre esto, así que prefiero detallarlo con honestidad.

Mi perfil profesional es más cercano al de arquitecto de soluciones e IT manager que al de programador de tiempo completo. Mi día a día está en arquitectura WordPress, infraestructura web y dirección IT en una universidad internacional. Programo cuando la solución lo requiere — automatización en Python, plugins en PHP, scripts de procesamiento — pero no escribo código de producción todos los días. La IA me permite operar a un nivel de salida que sin ella tomaría mucho más tiempo.

## Herramientas que usé

- **Claude (claude.ai)** como asistente principal de pensamiento: análisis del enunciado, definición del stack, diseño de la arquitectura, redacción del documento de especificación, revisión del código generado, preparación de defensa.
- **Codex (CLI de OpenAI)** como generador de código: a partir del documento de especificación, implementó archivos, modelos, lógica, tests y la UI demo.
- **VS Code** como editor para revisar y validar el código.

## Cómo fue el flujo de trabajo real

1. **Análisis del enunciado con Claude.** Discutí la prueba con Claude, definimos juntos el stack (Python + FastAPI + Pydantic + pytest + JSON), descartamos opciones (SQLAlchemy, Docker, autenticación) y acordamos la estructura de carpetas.
2. **Generación de un documento de especificación.** Claude me ayudó a redactar un `PROYECTO.md` con: stack decidido, estructura de archivos, modelos de datos, reglas de negocio enumeradas, festivos hardcodeados y orden de implementación.
3. **Implementación con Codex.** Le pasé el `PROYECTO.md` como contexto a Codex. Codex generó los archivos siguiendo esa especificación. Le pedí ajustes específicos (agregar la UI demo, ajustar mensajes, separar mejor algunos módulos).
4. **Revisión del código con Claude.** Volví a Claude con el código generado para revisar la calidad. Discutimos casos borde (qué pasa exactamente a las 24h antes, qué pasa con reservas consecutivas, qué pasa si un servicio referenciado ya no existe). Documentamos esos casos como decisiones explícitas en el README.
5. **Verificación.** Corrí `pytest -v` localmente y confirmé que todos los tests pasaban. Probé la API manualmente para verificar el flujo end-to-end.
6. **Decisión de no aplicar más cambios.** Identifiqué mejoras adicionales (mover `WORKING_WEEKDAYS` a constante, agregar logging extra), pero decidí no aplicarlas para entregar algo estable en lugar de pulir sin tiempo de verificar.

## Qué decisiones tomé yo

- Stack y descartes (Python + FastAPI vs alternativas, sin BD real, sin Docker).
- Separación de responsabilidades en módulos: `models`, `rules`, `repository`, `main`, `holidays`, `exceptions`.
- Agregar una UI demo opcional en `/`, decisión que no estaba pedida en la prueba pero que aporta valor de revisión.
- No aplicar mejoras de último momento; entregar algo estable y verificado.
- Reescribir esta nota de transparencia porque la primera versión generada era muy genérica.

## Qué decidió Codex (y yo aprobé al revisar)

- Uso de `price_cents` (centavos enteros) en lugar de floats para los montos. Cuando lo vi, lo aprobé porque evita errores de redondeo en cálculos monetarios — pero la idea fue de Codex, no mía.
- Inyección de `now` como parámetro en lugar de llamar a `datetime.now()` internamente. Lo aprobé porque hace los tests deterministas — pero también es decisión de Codex.
- Interpretación de los bordes inclusivo vs estricto (por ejemplo, "más de 24h" como `> 24` estricto). Cuando lo revisé con Claude, entendí por qué cada interpretación tiene sentido y lo dejé como estaba. Lo documenté como supuesto en el README.
- Capa de concurrencia con `threading.Lock` y escritura atómica vía archivo temporal.
- Parseo flexible de fechas en `ensure_bogota_datetime` para manejar las inconsistencias del seed.
- Estructura interna de los tests usando `pytest.mark.parametrize` para los tiers de reembolso.

## Limitaciones que reconozco

- No escribí línea por línea el código. No puedo defender cada detalle de implementación con la profundidad de quien lo escribió desde cero.
- Mi revisión del código fue principalmente estructural y de comportamiento (tests pasan, flujo funciona, decisiones documentadas) más que línea por línea.
- Hay partes del código — especialmente en el parseo flexible de fechas y en la capa de concurrencia — que entiendo en su intención pero no podría reescribir de memoria.

## Lo que sí puedo defender en entrevista

- Por qué cada archivo está donde está y qué responsabilidad tiene.
- Por qué se eligió cada decisión arquitectónica (stack, persistencia, separación de módulos).
- Qué hacen las funciones principales de `rules.py` y por qué cada regla se interpreta como se interpreta.
- Qué pasaría si me piden modificar la política de reembolso, agregar un nuevo tier de usuario, cambiar el horario de operación o agregar un nuevo tipo de servicio.
- Qué trade-offs tomé conscientemente y qué haría diferente con más tiempo.

## Reflexión final

La prueba evalúa, entre otras cosas, "que entiendas y puedas defender lo que entregues". Para mí eso significa entender el código a nivel de comportamiento, decisiones y consecuencias — no necesariamente a nivel de cada línea. Es la misma forma en que ejerzo mi rol actual de IT Director: dirigiendo, decidiendo y revisando, no escribiendo todo personalmente.

Si lo que están buscando es un perfil que programa Python todos los días desde cero, no soy yo. Si lo que están buscando es un perfil que entiende problemas, diseña soluciones y las ejecuta con las herramientas adecuadas — incluyendo IA como herramienta principal de productividad — entonces este ejercicio refleja honestamente cómo trabajo.
