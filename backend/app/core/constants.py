"""
Constantes globales utilizadas en toda la aplicación.
Centraliza valores fijos para evitar cadenas mágicas dispersas en el código.
"""


class RolesSistema:
    """Nombres de los roles disponibles en el sistema."""

    ADMINISTRADOR = "ADMINISTRADOR"
    RECEPCIONISTA = "RECEPCIONISTA"
    ESTILISTA = "ESTILISTA"
    CLIENTE = "CLIENTE"

    TODOS = [ADMINISTRADOR, RECEPCIONISTA, ESTILISTA, CLIENTE]


class EstadoCita:
    """Estados posibles de una cita."""

    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    EN_PROCESO = "EN_PROCESO"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"
    NO_ASISTIO = "NO_ASISTIO"

    TODOS = [PENDIENTE, CONFIRMADA, EN_PROCESO, FINALIZADA, CANCELADA, NO_ASISTIO]


class EstadoGenerico:
    """Estados genéricos reutilizables (activo/inactivo)."""

    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"

    TODOS = [ACTIVO, INACTIVO]


class MetodoPago:
    """Métodos de pago aceptados por el sistema."""

    EFECTIVO = "EFECTIVO"
    TARJETA = "TARJETA"
    TRANSFERENCIA = "TRANSFERENCIA"
    YAPE = "YAPE"
    PLIN = "PLIN"

    TODOS = [EFECTIVO, TARJETA, TRANSFERENCIA, YAPE, PLIN]


class EstadoPago:
    """Estados posibles de un pago."""

    PENDIENTE = "PENDIENTE"
    PARCIAL = "PARCIAL"
    COMPLETO = "COMPLETO"
    ANULADO = "ANULADO"

    TODOS = [PENDIENTE, PARCIAL, COMPLETO, ANULADO]


class EstadoVenta:
    """Estados posibles de una venta."""

    COMPLETADA = "COMPLETADA"
    ANULADA = "ANULADA"

    TODOS = [COMPLETADA, ANULADA]


class TipoMovimientoInventario:
    """Tipos de movimiento de inventario."""

    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"

    TODOS = [ENTRADA, SALIDA, AJUSTE]


class TipoComision:
    """Origen de una comisión."""

    SERVICIO = "SERVICIO"
    VENTA_PRODUCTO = "VENTA_PRODUCTO"

    TODOS = [SERVICIO, VENTA_PRODUCTO]


class EstadoComision:
    """Estado de pago de una comisión."""

    PENDIENTE = "PENDIENTE"
    PAGADA = "PAGADA"

    TODOS = [PENDIENTE, PAGADA]


class AccionAuditoria:
    """Acciones registradas en la tabla de auditoría."""

    CREAR = "CREAR"
    EDITAR = "EDITAR"
    ELIMINAR = "ELIMINAR"
    CANCELAR = "CANCELAR"
    PAGAR = "PAGAR"
    LOGIN = "LOGIN"
    LOGIN_FALLIDO = "LOGIN_FALLIDO"
    LOGOUT = "LOGOUT"

    TODOS = [CREAR, EDITAR, ELIMINAR, CANCELAR, PAGAR, LOGIN, LOGIN_FALLIDO, LOGOUT]
