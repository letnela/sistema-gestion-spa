"""Fase 13: portal del cliente

Revision ID: 0004_phase13_client_portal
Revises: 0003_phase8_inventory
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0004_phase13_client_portal"
down_revision="0003_phase8_inventory"
branch_labels=None
depends_on=None
def upgrade():
    op.add_column("usuarios", sa.Column("cliente_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_unique_constraint("uq_usuarios_cliente_id", "usuarios", ["cliente_id"])
    op.create_index("ix_usuarios_cliente_id", "usuarios", ["cliente_id"])
    op.create_foreign_key("fk_usuarios_cliente_id", "usuarios", "clientes", ["cliente_id"], ["id"], ondelete="SET NULL")
    op.execute("INSERT INTO roles (id,nombre,descripcion,created_at,updated_at) SELECT gen_random_uuid(),'CLIENTE','Portal de autoservicio para clientes',now(),now() WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre='CLIENTE')")
def downgrade():
    op.drop_constraint("fk_usuarios_cliente_id", "usuarios", type_="foreignkey")
    op.drop_index("ix_usuarios_cliente_id", table_name="usuarios")
    op.drop_constraint("uq_usuarios_cliente_id", "usuarios", type_="unique")
    op.drop_column("usuarios", "cliente_id")
