# Fase 17 - Corrección del módulo Recepcionista

## Accesos del recepcionista
- Inicio operativo propio
- Clientes
- Servicios (consulta)
- Empleados (consulta)
- Agenda
- Punto de venta
- Ventas
- Caja

## Accesos bloqueados
- Inventario
- Compras
- Comisiones
- Reportes administrativos
- Auditoría

Las restricciones están aplicadas tanto en el menú como en las rutas React. Escribir una URL restringida redirige al inicio permitido.

## Panel operativo
El inicio del recepcionista muestra:
- citas del día
- citas pendientes
- citas pendientes de cobro
- monto pendiente de cobro
- estado actual de caja
- accesos rápidos para registrar cliente, crear cita y cobrar

## Validación
- Compilación TypeScript/Vite correcta.
- Sintaxis Python correcta.
- Las pruebas unitarias independientes de PostgreSQL pasan.
- Las pruebas de autenticación requieren PostgreSQL activo en localhost:5432.
