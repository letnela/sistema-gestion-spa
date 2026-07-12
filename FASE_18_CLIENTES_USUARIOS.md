# Fase 18 — Clientes vinculados con usuarios del portal

## Flujo corregido

La ficha de cliente y la cuenta de acceso son entidades distintas, pero ahora se administran juntas.

Al crear un cliente desde Administración o Recepción se puede marcar **Crear acceso al portal**. El sistema crea, dentro de la misma transacción:

1. La ficha en `clientes`.
2. La cuenta en `usuarios` con rol `CLIENTE`.
3. La relación `usuarios.cliente_id`.

Si no se escribe una contraseña, se genera una temporal y se obliga al cliente a cambiarla.

## Acciones disponibles

- Crear acceso para un cliente existente.
- Activar o desactivar el acceso.
- Restablecer contraseña y mostrar una contraseña temporal una sola vez.
- Eliminar solo la cuenta del portal sin borrar la ficha del cliente.
- Sincronizar nombre, teléfono y correo entre la ficha y la cuenta.
- Al inactivar o archivar al cliente, su acceso también queda inactivo.

## Endpoints

- `POST /api/v1/clients/{cliente_id}/portal-access`
- `PATCH /api/v1/clients/{cliente_id}/portal-access/status`
- `POST /api/v1/clients/{cliente_id}/portal-access/reset-password`
- `DELETE /api/v1/clients/{cliente_id}/portal-access`

No requiere migración nueva porque `usuarios.cliente_id` ya fue agregado en la Fase 13.
