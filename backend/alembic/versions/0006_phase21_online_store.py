"""Fase 21: tienda online responsive para clientes.
Revision ID: 0006_phase21_online_store
Revises: 0005_phase15_commercial_erp
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='0006_phase21_online_store'
down_revision='0005_phase15_commercial_erp'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('pedidos_online',
      sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column('cliente_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('clientes.id',ondelete='CASCADE'),nullable=False),
      sa.Column('codigo',sa.String(40),nullable=False,unique=True),
      sa.Column('estado',sa.String(30),nullable=False,server_default='PENDIENTE'),
      sa.Column('subtotal',sa.Numeric(10,2),nullable=False),
      sa.Column('descuento',sa.Numeric(10,2),nullable=False,server_default='0'),
      sa.Column('total',sa.Numeric(10,2),nullable=False),
      sa.Column('modalidad_entrega',sa.String(30),nullable=False,server_default='RECOJO_SALON'),
      sa.Column('direccion_entrega',sa.String(300)),
      sa.Column('metodo_pago',sa.String(30),nullable=False,server_default='PAGO_EN_SALON'),
      sa.Column('notas',sa.Text()),
      sa.Column('fecha',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
      sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
      sa.Column('updated_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_index('ix_pedidos_online_cliente_id','pedidos_online',['cliente_id'])
    op.create_index('ix_pedidos_online_codigo','pedidos_online',['codigo'],unique=True)
    op.create_table('pedido_online_detalles',
      sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column('pedido_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('pedidos_online.id',ondelete='CASCADE'),nullable=False),
      sa.Column('producto_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('productos.id',ondelete='RESTRICT'),nullable=False),
      sa.Column('cantidad',sa.Integer(),nullable=False),
      sa.Column('precio_unitario',sa.Numeric(10,2),nullable=False),
      sa.Column('subtotal',sa.Numeric(10,2),nullable=False))

def downgrade():
    op.drop_table('pedido_online_detalles')
    op.drop_index('ix_pedidos_online_codigo',table_name='pedidos_online')
    op.drop_index('ix_pedidos_online_cliente_id',table_name='pedidos_online')
    op.drop_table('pedidos_online')
