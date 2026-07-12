# Fase 19 — Experiencia premium y datos profesionales

## Mejoras de Clientes
- Fichas con datos completos, preferencias, alergias y acceso al portal.
- Clientes demo realistas con domicilios, teléfonos y observaciones coherentes.
- Seis clientes con cuenta lista para probar el portal.
- Vinculación cliente/usuario mantenida en una sola operación.

## Mejoras de Productos
- Vista exclusiva de inventario con indicadores.
- Categorías y proveedores seleccionables; ya no se escriben UUID.
- Costo, precio, margen, stock mínimo/máximo y detalle profesional.
- 30 productos profesionales distribuidos en seis categorías.
- Kardex inicial y movimientos de venta consistentes.

## Datos completos
- 4 roles y usuarios internos.
- 15 clientes y 6 cuentas de portal.
- 21 servicios y 5 profesionales con horarios y especialidades.
- 5 proveedores, 30 productos y kardex.
- Citas pasadas y futuras con distintos estados.
- Ventas vinculadas a citas, pagos y movimientos de caja.
- Comisiones, compras, promociones y configuración comercial.

## Reset controlado

```powershell
python -m app.seed.professional_seed --confirm-reset
```

Este comando borra la data anterior y vuelve a cargar el escenario profesional completo. No elimina las migraciones ni la estructura de la base de datos.
