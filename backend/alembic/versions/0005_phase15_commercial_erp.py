"""Fase 15: vincular ventas con citas

Revision ID: 0005_phase15_commercial_erp
Revises: 0004_phase13_client_portal
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0005_phase15_commercial_erp"
down_revision="0004_phase13_client_portal"
branch_labels=None
depends_on=None
def upgrade():
    op.add_column("ventas",sa.Column("cita_id",postgresql.UUID(as_uuid=True),nullable=True))
    op.create_unique_constraint("uq_ventas_cita_id","ventas",["cita_id"])
    op.create_index("ix_ventas_cita_id","ventas",["cita_id"])
    op.create_foreign_key("fk_ventas_cita_id","ventas","citas",["cita_id"],["id"],ondelete="SET NULL")
def downgrade():
    op.drop_constraint("fk_ventas_cita_id","ventas",type_="foreignkey")
    op.drop_index("ix_ventas_cita_id",table_name="ventas")
    op.drop_constraint("uq_ventas_cita_id","ventas",type_="unique")
    op.drop_column("ventas","cita_id")
