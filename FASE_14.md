# Fase 14 — Agenda avanzada por rol

## Administrador
- Consulta toda la agenda y sus indicadores.
- Crea, edita, confirma, cancela y elimina citas.
- Puede consultar cualquier empleado y cliente.

## Recepcionista
- Consulta la agenda general.
- Crea, edita, confirma, cancela y marca inasistencia.
- No elimina citas ni finaliza servicios.

## Estilista
- Al ingresar es enviado directamente a **Mi agenda**.
- El backend filtra automáticamente por el empleado vinculado a su usuario.
- Solo puede consultar citas propias.
- Puede iniciar una cita confirmada, finalizar una cita en proceso y marcar inasistencia.
- No ve clientes, empleados, inventario, caja, compras ni reportes administrativos.

## Cliente
- Selecciona servicios visualmente.
- Solo ve profesionales que realizan todos los servicios elegidos.
- Consulta horarios realmente disponibles.
- Reserva, reprograma y cancela únicamente sus propias citas.

## Seguridad
Los permisos se validan en FastAPI. Ocultar botones o escribir manualmente otra URL no permite saltarse las restricciones.
