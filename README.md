# Booking Service

API HTTP para gestionar reservas de citas, creada como solución a la prueba técnica de Desarrollador IA.

## Requisitos

- Python 3.11 o superior
- Git

## Instalación

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Correr la API

```bash
uvicorn app.main:app --reload
```

Luego abrir:

- Interfaz demo: `http://localhost:8000`
- API: `http://localhost:8000`
- Documentación interactiva: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/api/v1/health`

La interfaz demo permite crear, listar y cancelar reservas usando la misma API. Es una capa visual opcional para facilitar la revisión; las reglas de negocio siguen viviendo en el backend.

## Correr pruebas

```bash
pytest -v
```

## Endpoints

### Crear reserva

`POST /api/v1/bookings`

```json
{
  "user_id": "u-001",
  "service_id": "s-003",
  "start_at": "2026-05-19T10:00:00-05:00"
}
```

### Cancelar reserva

`DELETE /api/v1/bookings/{booking_id}`

La respuesta incluye el porcentaje y los montos calculados:

```json
{
  "id": "b-001",
  "status": "cancelled",
  "refund_percentage": 50,
  "refund_amount_cents": 6000000,
  "charged_amount_cents": 6000000,
  "cancelled_at": "2026-05-15T08:00:00-05:00"
}
```

### Listar reservas de un usuario

`GET /api/v1/users/{user_id}/bookings?from=2026-05-19T00:00:00-05:00&to=2026-05-20T23:59:59-05:00`

### Catálogo para interfaz demo

- `GET /api/v1/users`
- `GET /api/v1/services`

## Decisiones técnicas

Elegí Python con FastAPI porque permite construir una API pequeña, clara y testeable en poco tiempo. FastAPI también genera documentación OpenAPI automáticamente en `/docs`, útil para revisar la solución durante la entrevista.

La lógica de negocio está en `app/rules.py`, separada de la API. Esto permite probar las reglas sin levantar el servidor y facilita explicar el flujo.

Usé persistencia en archivo JSON (`data/seed.json`) porque la prueba no exige base de datos real. Para concurrencia básica, el repositorio usa un lock de proceso y escritura atómica con archivo temporal.

Todas las fechas se normalizan a `America/Bogota`. Si una fecha viene sin zona horaria en el seed, se asume hora local de Bogotá.

## Supuestos tomados

- El profesional está asociado al servicio mediante `professional_id`, porque la creación de reserva solo recibe usuario, servicio y fecha/hora.
- Cada servicio tiene `price_cents`, necesario para calcular el monto a cobrar o reembolsar al cancelar.
- La reserva debe empezar y terminar dentro del horario 7:00 a 19:00. Terminar exactamente a las 19:00 es válido.
- Los festivos de Colombia 2026 están hardcodeados.
- Las reservas canceladas y las pasadas no cuentan para el límite de 3 reservas activas futuras.
- Una reserva activa puede cancelarse incluso si ya está muy cerca de iniciar; el reembolso será 0 cuando aplique.
- Los montos se guardan en centavos para evitar errores de punto flotante.

## Reglas de reembolso

Servicios `non_refundable`: siempre 0% de reembolso, sin importar usuario ni anticipación.

Usuarios standard:

- Más de 24 horas antes: 100%
- Desde 24 horas hasta 4 horas antes: 50%
- Menos de 4 horas antes: 0%

Usuarios premium:

- 4 horas o más antes: 100%
- Desde 1 hora hasta menos de 4 horas antes: 50%
- Menos de 1 hora antes: 0%

## Manejo de datos inconsistentes

El archivo `data/seed.json` incluye fechas en varios formatos y un registro inválido. El repositorio intenta parsear:

- ISO 8601
- `YYYY-MM-DD HH:MM`
- `DD/MM/YYYY HH:MM`

Si un registro no se puede interpretar o le falta un dato crítico, se descarta con un warning de logging. La aplicación no falla completa por un registro defectuoso.

## Qué dejé por fuera

- Autenticación y autorización: no estaban requeridas.
- Base de datos real: para el alcance de 4 a 6 horas, JSON es suficiente.
- Concurrencia distribuida: el lock actual cubre concurrencia básica dentro del proceso.
- Cálculo dinámico de festivos: se pidió explícitamente que podía usarse una lista hardcodeada.

## Qué haría diferente con más tiempo

- Migrar persistencia a PostgreSQL.
- Agregar migraciones y constraints para evitar solapamientos desde base de datos.
- Añadir logs estructurados y trazabilidad por request.
- Agregar más pruebas de concurrencia.
- Calcular festivos con una librería o servicio confiable.
