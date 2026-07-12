# Fase 15 — ERP comercial por roles

## ADMINISTRADOR
- POS, ventas, caja, comisiones, reportes y auditoría.
- Pago de comisiones y reapertura controlada de caja.

## RECEPCIONISTA
- POS, cobro de citas finalizadas, ventas, caja e historial operativo.
- No accede a auditoría ni puede pagar comisiones.

## ESTILISTA
- Solo su agenda y sus comisiones.
- No accede a caja, POS o finanzas generales.

## CLIENTE
- Sus citas, perfil, compras y comprobantes PDF.

## Migración
Ejecutar `alembic upgrade head` para agregar `ventas.cita_id`.
