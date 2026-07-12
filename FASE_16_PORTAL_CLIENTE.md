# Fase 16 - Portal completo del cliente

## Funciones
- Registro público con rol CLIENTE y ficha vinculada.
- Inicio exclusivo con próximas citas e indicadores.
- Catálogo de servicios, precios, duración y promociones vigentes.
- Reserva guiada: servicios, profesional compatible, fecha y horario disponible.
- Validación de horarios, descansos, vacaciones, bloqueos y cruces en backend.
- Listado exclusivo de citas propias.
- Reprogramación y cancelación de citas pendientes o confirmadas.
- Perfil editable con preferencias y alergias.
- Historial de compras y comprobantes PDF.
- Separación total del panel administrativo y protección por rol en backend.

## Ejecución
Backend: `alembic upgrade head` y `uvicorn app.main:app --reload`.
Frontend: `npm install --no-audit --no-fund` y `npm run dev`.

No requiere migración adicional si ya se aplicó la Fase 15.
