"""Memoria de sesión del asistente virtual (chat_mensajes).
Revision ID: 0007_chat_memory
Revises: 0006_phase21_online_store
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = '0007_chat_memory'
down_revision = '0006_phase21_online_store'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('chat_mensajes',
      sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
      sa.Column('sesion_id', sa.String(100), nullable=False),
      sa.Column('role', sa.String(20), nullable=False),
      sa.Column('contenido', sa.Text(), nullable=False),
      sa.Column('fecha', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index('ix_chat_mensajes_sesion_id', 'chat_mensajes', ['sesion_id'])


def downgrade():
    op.drop_index('ix_chat_mensajes_sesion_id', table_name='chat_mensajes')
    op.drop_table('chat_mensajes')
