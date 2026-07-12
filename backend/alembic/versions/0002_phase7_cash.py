"""Fase 7: sesiones y movimientos de caja.

Revision ID: 0002_phase7_cash
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_phase7_cash"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("caja_sesiones",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column("usuario_apertura_id",postgresql.UUID(as_uuid=True),nullable=False),
        sa.Column("usuario_cierre_id",postgresql.UUID(as_uuid=True),nullable=True),
        sa.Column("fecha_apertura",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.Column("fecha_cierre",sa.DateTime(timezone=True),nullable=True),
        sa.Column("monto_apertura",sa.Numeric(10,2),nullable=False),
        sa.Column("monto_cierre_declarado",sa.Numeric(10,2),nullable=True),
        sa.Column("monto_cierre_calculado",sa.Numeric(10,2),nullable=True),
        sa.Column("diferencia",sa.Numeric(10,2),nullable=True),
        sa.Column("estado",sa.String(20),server_default="ABIERTA",nullable=False),
        sa.Column("observaciones",sa.Text(),nullable=True),
        sa.ForeignKeyConstraint(["usuario_apertura_id"],["usuarios.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_cierre_id"],["usuarios.id"],ondelete="RESTRICT"),
        sa.CheckConstraint("estado IN ('ABIERTA','CERRADA')",name="ck_caja_sesion_estado"),
        sa.CheckConstraint("monto_apertura >= 0",name="ck_caja_apertura_no_negativa"))
    op.create_table("caja_movimientos",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column("caja_sesion_id",postgresql.UUID(as_uuid=True),nullable=False),
        sa.Column("usuario_id",postgresql.UUID(as_uuid=True),nullable=False),
        sa.Column("tipo",sa.String(20),nullable=False),sa.Column("concepto",sa.String(200),nullable=False),
        sa.Column("monto",sa.Numeric(10,2),nullable=False),sa.Column("referencia",sa.String(150),nullable=True),
        sa.Column("fecha",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.ForeignKeyConstraint(["caja_sesion_id"],["caja_sesiones.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"],["usuarios.id"],ondelete="RESTRICT"),
        sa.CheckConstraint("tipo IN ('INGRESO','EGRESO')",name="ck_caja_movimiento_tipo"),
        sa.CheckConstraint("monto > 0",name="ck_caja_movimiento_monto_positivo"))
    op.create_index("ix_caja_sesiones_estado","caja_sesiones",["estado"])
    op.create_index("ix_caja_movimientos_fecha","caja_movimientos",["fecha"])

def downgrade():
    op.drop_index("ix_caja_movimientos_fecha",table_name="caja_movimientos")
    op.drop_table("caja_movimientos")
    op.drop_index("ix_caja_sesiones_estado",table_name="caja_sesiones")
    op.drop_table("caja_sesiones")
