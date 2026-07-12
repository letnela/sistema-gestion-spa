"""esquema inicial completo del sistema de gestion de salon de belleza

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # roles
    # ------------------------------------------------------------------
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(50), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("nombre", name="uq_roles_nombre"),
    )
    op.create_index("ix_roles_nombre", "roles", ["nombre"])

    # ------------------------------------------------------------------
    # usuarios
    # ------------------------------------------------------------------
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre_completo", sa.String(150), nullable=False),
        sa.Column("correo", sa.String(150), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("rol_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("ultimo_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("debe_cambiar_password", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("intentos_fallidos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reset_password_token", sa.String(255), nullable=True),
        sa.Column("reset_password_expira", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["rol_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("correo", name="uq_usuarios_correo"),
    )
    op.create_index("ix_usuarios_correo", "usuarios", ["correo"])

    # ------------------------------------------------------------------
    # intentos_login
    # ------------------------------------------------------------------
    op.create_table(
        "intentos_login",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("correo_intentado", sa.String(150), nullable=False),
        sa.Column("exitoso", sa.Boolean(), nullable=False),
        sa.Column("ip_origen", sa.String(50), nullable=True),
        sa.Column("navegador", sa.String(255), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
    )

    # ------------------------------------------------------------------
    # clientes
    # ------------------------------------------------------------------
    op.create_table(
        "clientes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombres", sa.String(100), nullable=False),
        sa.Column("apellidos", sa.String(100), nullable=False),
        sa.Column("documento", sa.String(30), nullable=True),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.Column("correo", sa.String(150), nullable=True),
        sa.Column("direccion", sa.String(255), nullable=True),
        sa.Column("fecha_nacimiento", sa.Date(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("preferencias", sa.Text(), nullable=True),
        sa.Column("alergias", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("eliminado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("documento", name="uq_clientes_documento"),
    )

    # ------------------------------------------------------------------
    # empleados
    # ------------------------------------------------------------------
    op.create_table(
        "empleados",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("nombres", sa.String(100), nullable=False),
        sa.Column("apellidos", sa.String(100), nullable=False),
        sa.Column("documento", sa.String(30), nullable=True),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.Column("correo", sa.String(150), nullable=True),
        sa.Column("cargo", sa.String(100), nullable=False),
        sa.Column("especialidad", sa.String(150), nullable=True),
        sa.Column("salario", sa.Numeric(10, 2), nullable=True),
        sa.Column("porcentaje_comision_default", sa.Numeric(5, 2), nullable=False),
        sa.Column("fecha_ingreso", sa.Date(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("usuario_id", name="uq_empleados_usuario"),
        sa.UniqueConstraint("documento", name="uq_empleados_documento"),
    )

    # ------------------------------------------------------------------
    # categorias_servicio / servicios
    # ------------------------------------------------------------------
    op.create_table(
        "categorias_servicio",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("nombre", name="uq_categorias_servicio_nombre"),
    )

    op.create_table(
        "servicios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("categoria_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("precio", sa.Numeric(10, 2), nullable=False),
        sa.Column("duracion_minutos", sa.Integer(), nullable=False),
        sa.Column("imagen_url", sa.String(500), nullable=True),
        sa.Column("porcentaje_comision", sa.Numeric(5, 2), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["categoria_id"], ["categorias_servicio.id"], ondelete="RESTRICT"),
    )

    # ------------------------------------------------------------------
    # empleado_servicio / horarios / vacaciones / bloqueos
    # ------------------------------------------------------------------
    op.create_table(
        "empleado_servicio",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empleado_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("servicio_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["empleado_id"], ["empleados.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("empleado_id", "servicio_id", name="uq_empleado_servicio"),
    )

    op.create_table(
        "horarios_empleado",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empleado_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dia_semana", sa.Integer(), nullable=False),
        sa.Column("hora_entrada", sa.Time(), nullable=False),
        sa.Column("hora_salida", sa.Time(), nullable=False),
        sa.Column("hora_inicio_descanso", sa.Time(), nullable=True),
        sa.Column("hora_fin_descanso", sa.Time(), nullable=True),
        sa.Column("es_dia_libre", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["empleado_id"], ["empleados.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("empleado_id", "dia_semana", name="uq_horario_empleado_dia"),
        sa.CheckConstraint("dia_semana >= 1 AND dia_semana <= 7", name="ck_horarios_dia_valido"),
    )

    op.create_table(
        "vacaciones_empleado",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empleado_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=False),
        sa.Column("motivo", sa.String(255), nullable=True),
        sa.Column("aprobado", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["empleado_id"], ["empleados.id"], ondelete="CASCADE"),
        sa.CheckConstraint("fecha_fin >= fecha_inicio", name="ck_vacaciones_fechas_validas"),
    )

    op.create_table(
        "bloqueos_horario",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empleado_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora_inicio", sa.Time(), nullable=False),
        sa.Column("hora_fin", sa.Time(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["empleado_id"], ["empleados.id"], ondelete="CASCADE"),
    )

    # ------------------------------------------------------------------
    # categorias_producto / proveedores / productos / proveedor_producto
    # ------------------------------------------------------------------
    op.create_table(
        "categorias_producto",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("nombre", name="uq_categorias_producto_nombre"),
    )

    op.create_table(
        "proveedores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("razon_social", sa.String(150), nullable=False),
        sa.Column("documento_ruc", sa.String(30), nullable=False),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.Column("correo", sa.String(150), nullable=True),
        sa.Column("direccion", sa.String(255), nullable=True),
        sa.Column("contacto_nombre", sa.String(150), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("documento_ruc", name="uq_proveedores_ruc"),
    )

    op.create_table(
        "productos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("categoria_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("proveedor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("marca", sa.String(100), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("precio_compra", sa.Numeric(10, 2), nullable=False),
        sa.Column("precio_venta", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stock_minimo", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("imagen_url", sa.String(500), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["categoria_id"], ["categorias_producto.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proveedor_id"], ["proveedores.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("codigo", name="uq_productos_codigo"),
        sa.CheckConstraint("stock >= 0", name="ck_productos_stock_no_negativo"),
    )
    op.create_index("ix_productos_codigo", "productos", ["codigo"])

    op.create_table(
        "proveedor_producto",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("proveedor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("producto_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["proveedor_id"], ["proveedores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("proveedor_id", "producto_id", name="uq_proveedor_producto"),
    )

    # ------------------------------------------------------------------
    # citas / cita_servicios
    # ------------------------------------------------------------------
    op.create_table(
        "citas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empleado_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora_inicio", sa.Time(), nullable=False),
        sa.Column("hora_fin", sa.Time(), nullable=False),
        sa.Column("duracion_total_minutos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("precio_total", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("motivo_cancelacion", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empleado_id"], ["empleados.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "estado IN ('PENDIENTE','CONFIRMADA','EN_PROCESO','FINALIZADA','CANCELADA','NO_ASISTIO')",
            name="ck_citas_estado_valido",
        ),
    )
    op.create_index("ix_citas_fecha", "citas", ["fecha"])
    op.create_index("ix_citas_empleado_fecha", "citas", ["empleado_id", "fecha"])

    op.create_table(
        "cita_servicios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cita_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("servicio_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("precio_aplicado", sa.Numeric(10, 2), nullable=False),
        sa.Column("duracion_aplicada_minutos", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["cita_id"], ["citas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"], ondelete="RESTRICT"),
    )

    # ------------------------------------------------------------------
    # inventario_movimientos
    # ------------------------------------------------------------------
    op.create_table(
        "inventario_movimientos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("producto_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("stock_resultante", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("tipo IN ('ENTRADA','SALIDA','AJUSTE')", name="ck_inventario_tipo_valido"),
        sa.CheckConstraint("stock_resultante >= 0", name="ck_inventario_stock_no_negativo"),
    )

    # ------------------------------------------------------------------
    # ventas / venta_detalles
    # ------------------------------------------------------------------
    op.create_table(
        "ventas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("numero_comprobante", sa.String(50), nullable=False),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("descuento", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("impuesto", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("motivo_anulacion", sa.String(255), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["usuarios.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("numero_comprobante", name="uq_ventas_comprobante"),
        sa.CheckConstraint("estado IN ('COMPLETADA','ANULADA')", name="ck_ventas_estado_valido"),
    )
    op.create_index("ix_ventas_numero_comprobante", "ventas", ["numero_comprobante"])
    op.create_index("ix_ventas_fecha", "ventas", ["fecha"])

    op.create_table(
        "venta_detalles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("venta_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("producto_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("servicio_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("empleado_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cantidad", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("precio_unitario", sa.Numeric(10, 2), nullable=False),
        sa.Column("descuento", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(["venta_id"], ["ventas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empleado_id"], ["empleados.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "(producto_id IS NOT NULL AND servicio_id IS NULL) OR "
            "(producto_id IS NULL AND servicio_id IS NOT NULL)",
            name="ck_venta_detalle_producto_o_servicio",
        ),
    )

    # ------------------------------------------------------------------
    # pagos
    # ------------------------------------------------------------------
    op.create_table(
        "pagos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("venta_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False),
        sa.Column("metodo", sa.String(30), nullable=False),
        sa.Column("referencia", sa.String(150), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["venta_id"], ["ventas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "metodo IN ('EFECTIVO','TARJETA','TRANSFERENCIA','YAPE','PLIN')",
            name="ck_pagos_metodo_valido",
        ),
        sa.CheckConstraint(
            "estado IN ('PENDIENTE','PARCIAL','COMPLETO','ANULADO')", name="ck_pagos_estado_valido"
        ),
        sa.CheckConstraint("monto > 0", name="ck_pagos_monto_positivo"),
    )

    # ------------------------------------------------------------------
    # promociones / promocion_servicios / promocion_productos
    # ------------------------------------------------------------------
    op.create_table(
        "promociones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("porcentaje_descuento", sa.Numeric(5, 2), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("fecha_fin >= fecha_inicio", name="ck_promociones_fechas_validas"),
        sa.CheckConstraint(
            "porcentaje_descuento > 0 AND porcentaje_descuento <= 100",
            name="ck_promociones_descuento_valido",
        ),
    )

    op.create_table(
        "promocion_servicios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("promocion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("servicio_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["promocion_id"], ["promociones.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("promocion_id", "servicio_id", name="uq_promocion_servicio"),
    )

    op.create_table(
        "promocion_productos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("promocion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("producto_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["promocion_id"], ["promociones.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("promocion_id", "producto_id", name="uq_promocion_producto"),
    )

    # ------------------------------------------------------------------
    # comisiones
    # ------------------------------------------------------------------
    op.create_table(
        "comisiones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empleado_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("venta_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("monto_base", sa.Numeric(10, 2), nullable=False),
        sa.Column("porcentaje_aplicado", sa.Numeric(5, 2), nullable=False),
        sa.Column("monto_comision", sa.Numeric(10, 2), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("periodo", sa.Date(), nullable=False),
        sa.Column("fecha_pago", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["empleado_id"], ["empleados.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["venta_id"], ["ventas.id"], ondelete="SET NULL"),
        sa.CheckConstraint("tipo IN ('SERVICIO','VENTA_PRODUCTO')", name="ck_comisiones_tipo_valido"),
        sa.CheckConstraint("estado IN ('PENDIENTE','PAGADA')", name="ck_comisiones_estado_valido"),
    )

    # ------------------------------------------------------------------
    # auditoria / notificaciones
    # ------------------------------------------------------------------
    op.create_table(
        "auditoria",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("accion", sa.String(30), nullable=False),
        sa.Column("modulo", sa.String(100), nullable=False),
        sa.Column("entidad", sa.String(100), nullable=False),
        sa.Column("entidad_id", sa.String(100), nullable=True),
        sa.Column("valor_anterior", postgresql.JSONB(), nullable=True),
        sa.Column("valor_nuevo", postgresql.JSONB(), nullable=True),
        sa.Column("ip_origen", sa.String(50), nullable=True),
        sa.Column("navegador", sa.String(255), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_auditoria_fecha", "auditoria", ["fecha"])
    op.create_index("ix_auditoria_entidad", "auditoria", ["entidad", "entidad_id"])

    op.create_table(
        "notificaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("titulo", sa.String(150), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("leida", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tipo", sa.String(50), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
    )

    # ------------------------------------------------------------------
    # configuracion_salon
    # ------------------------------------------------------------------
    op.create_table(
        "configuracion_salon",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre_salon", sa.String(150), nullable=False),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("ruc", sa.String(30), nullable=True),
        sa.Column("direccion", sa.String(255), nullable=True),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.Column("correo", sa.String(150), nullable=True),
        sa.Column("moneda", sa.String(10), nullable=False),
        sa.Column("impuesto_porcentaje", sa.Numeric(5, 2), nullable=False),
        sa.Column("horario_general", sa.String(255), nullable=True),
        sa.Column("color_principal", sa.String(20), nullable=False),
        sa.Column("texto_comprobante", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("configuracion_salon")
    op.drop_table("notificaciones")
    op.drop_index("ix_auditoria_entidad", table_name="auditoria")
    op.drop_index("ix_auditoria_fecha", table_name="auditoria")
    op.drop_table("auditoria")
    op.drop_table("comisiones")
    op.drop_table("promocion_productos")
    op.drop_table("promocion_servicios")
    op.drop_table("promociones")
    op.drop_table("pagos")
    op.drop_table("venta_detalles")
    op.drop_index("ix_ventas_fecha", table_name="ventas")
    op.drop_index("ix_ventas_numero_comprobante", table_name="ventas")
    op.drop_table("ventas")
    op.drop_table("inventario_movimientos")
    op.drop_table("cita_servicios")
    op.drop_index("ix_citas_empleado_fecha", table_name="citas")
    op.drop_index("ix_citas_fecha", table_name="citas")
    op.drop_table("citas")
    op.drop_table("proveedor_producto")
    op.drop_index("ix_productos_codigo", table_name="productos")
    op.drop_table("productos")
    op.drop_table("proveedores")
    op.drop_table("categorias_producto")
    op.drop_table("bloqueos_horario")
    op.drop_table("vacaciones_empleado")
    op.drop_table("horarios_empleado")
    op.drop_table("empleado_servicio")
    op.drop_table("servicios")
    op.drop_table("categorias_servicio")
    op.drop_table("empleados")
    op.drop_table("clientes")
    op.drop_table("intentos_login")
    op.drop_index("ix_usuarios_correo", table_name="usuarios")
    op.drop_table("usuarios")
    op.drop_index("ix_roles_nombre", table_name="roles")
    op.drop_table("roles")
