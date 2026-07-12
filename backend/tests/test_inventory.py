from decimal import Decimal
from uuid import uuid4
import pytest
from pydantic import ValidationError
from app.schemas.inventory_schema import ProductoCrear, AjusteInventarioRequest, CompraCrear, CompraDetalleCrear, ProveedorCrear

def test_producto_valido():
    p=ProductoCrear(categoria_id=uuid4(),nombre='Shampoo profesional',precio_compra=Decimal('20'),precio_venta=Decimal('35'),stock_minimo=5,stock_maximo=30)
    assert p.unidad_medida=='UNIDAD'
def test_stock_maximo_invalido():
    with pytest.raises(ValidationError): ProductoCrear(categoria_id=uuid4(),nombre='Producto',precio_compra=1,precio_venta=2,stock_minimo=10,stock_maximo=5)
def test_ajuste_salida_positivo():
    x=AjusteInventarioRequest(producto_id=uuid4(),cantidad=2,tipo='salida',motivo='Consumo interno'); assert x.tipo=='SALIDA'
def test_ajuste_cantidad_invalida():
    with pytest.raises(ValidationError): AjusteInventarioRequest(producto_id=uuid4(),cantidad=0,tipo='ENTRADA',motivo='Prueba')
def test_compra_requiere_detalles():
    with pytest.raises(ValidationError): CompraCrear(proveedor_id=uuid4(),detalles=[])
def test_proveedor_email_valido():
    p=ProveedorCrear(razon_social='Distribuidora Belleza SAC',documento_ruc='20123456789',correo='ventas@belleza.pe'); assert str(p.correo)=='ventas@belleza.pe'
