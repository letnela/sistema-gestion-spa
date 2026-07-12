"""Fase 8: ampliación de inventario y módulo de compras."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='0003_phase8_inventory'; down_revision='0002_phase7_cash'; branch_labels=None; depends_on=None

def upgrade():
    op.add_column('productos',sa.Column('codigo_barras',sa.String(100),nullable=True))
    op.add_column('productos',sa.Column('unidad_medida',sa.String(30),nullable=False,server_default='UNIDAD'))
    op.add_column('productos',sa.Column('stock_maximo',sa.Integer(),nullable=True))
    op.add_column('productos',sa.Column('fecha_vencimiento',sa.Date(),nullable=True))
    op.create_unique_constraint('uq_productos_codigo_barras','productos',['codigo_barras'])
    op.create_index('ix_productos_codigo_barras','productos',['codigo_barras'])
    op.create_check_constraint('ck_productos_stock_maximo','productos','stock_maximo IS NULL OR stock_maximo >= stock_minimo')
    op.create_table('compras',
      sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('numero_compra',sa.String(50),nullable=False),
      sa.Column('proveedor_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('usuario_id',postgresql.UUID(as_uuid=True),nullable=False),
      sa.Column('subtotal',sa.Numeric(12,2),nullable=False,server_default='0'),sa.Column('descuento',sa.Numeric(12,2),nullable=False,server_default='0'),
      sa.Column('impuesto',sa.Numeric(12,2),nullable=False,server_default='0'),sa.Column('total',sa.Numeric(12,2),nullable=False,server_default='0'),
      sa.Column('estado',sa.String(20),nullable=False,server_default='RECIBIDA'),sa.Column('observaciones',sa.Text(),nullable=True),
      sa.Column('fecha',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
      sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
      sa.ForeignKeyConstraint(['proveedor_id'],['proveedores.id'],ondelete='RESTRICT'),sa.ForeignKeyConstraint(['usuario_id'],['usuarios.id'],ondelete='RESTRICT'),
      sa.UniqueConstraint('numero_compra',name='uq_compras_numero'),sa.CheckConstraint("estado IN ('RECIBIDA','ANULADA')",name='ck_compras_estado'))
    op.create_index('ix_compras_numero_compra','compras',['numero_compra']); op.create_index('ix_compras_fecha','compras',['fecha'])
    op.create_table('compra_detalles',
      sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('compra_id',postgresql.UUID(as_uuid=True),nullable=False),
      sa.Column('producto_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('cantidad',sa.Integer(),nullable=False),
      sa.Column('costo_unitario',sa.Numeric(12,2),nullable=False),sa.Column('descuento',sa.Numeric(12,2),nullable=False,server_default='0'),sa.Column('subtotal',sa.Numeric(12,2),nullable=False),
      sa.ForeignKeyConstraint(['compra_id'],['compras.id'],ondelete='CASCADE'),sa.ForeignKeyConstraint(['producto_id'],['productos.id'],ondelete='RESTRICT'),
      sa.CheckConstraint('cantidad > 0',name='ck_compra_detalle_cantidad'),sa.CheckConstraint('costo_unitario > 0',name='ck_compra_detalle_costo'))

def downgrade():
    op.drop_table('compra_detalles'); op.drop_index('ix_compras_fecha',table_name='compras'); op.drop_index('ix_compras_numero_compra',table_name='compras'); op.drop_table('compras')
    op.drop_constraint('ck_productos_stock_maximo','productos',type_='check'); op.drop_index('ix_productos_codigo_barras',table_name='productos'); op.drop_constraint('uq_productos_codigo_barras','productos',type_='unique')
    op.drop_column('productos','fecha_vencimiento'); op.drop_column('productos','stock_maximo'); op.drop_column('productos','unidad_medida'); op.drop_column('productos','codigo_barras')
