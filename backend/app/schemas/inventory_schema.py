"""Esquemas de productos, proveedores, compras e inventario."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from app.core.constants import EstadoGenerico

class CategoriaProductoCrear(BaseModel):
    nombre: str = Field(min_length=2,max_length=100)
    descripcion: str|None=None
    @field_validator('nombre')
    @classmethod
    def clean(cls,v): return ' '.join(v.strip().split())
class CategoriaProductoActualizar(BaseModel):
    nombre:str|None=Field(None,min_length=2,max_length=100); descripcion:str|None=None; estado:str|None=None
class CategoriaProductoResponse(BaseModel):
    id:uuid.UUID; nombre:str; descripcion:str|None; estado:str
    model_config={'from_attributes':True}

class ProveedorCrear(BaseModel):
    razon_social:str=Field(min_length=2,max_length=150); documento_ruc:str=Field(min_length=8,max_length=30)
    telefono:str|None=Field(None,max_length=30); correo:EmailStr|None=None; direccion:str|None=None; contacto_nombre:str|None=None
    @field_validator('razon_social','documento_ruc')
    @classmethod
    def clean(cls,v): return ' '.join(v.strip().split())
class ProveedorActualizar(BaseModel):
    razon_social:str|None=None; documento_ruc:str|None=None; telefono:str|None=None; correo:EmailStr|None=None; direccion:str|None=None; contacto_nombre:str|None=None; estado:str|None=None
class ProveedorResponse(BaseModel):
    id:uuid.UUID; razon_social:str; documento_ruc:str; telefono:str|None; correo:str|None; direccion:str|None; contacto_nombre:str|None; estado:str
    model_config={'from_attributes':True}

class ProductoCrear(BaseModel):
    categoria_id:uuid.UUID; proveedor_id:uuid.UUID|None=None; codigo:str|None=Field(None,max_length=50); codigo_barras:str|None=Field(None,max_length=100)
    nombre:str=Field(min_length=2,max_length=150); marca:str|None=None; descripcion:str|None=None
    precio_compra:Decimal=Field(ge=0); precio_venta:Decimal=Field(gt=0); stock:int=Field(default=0,ge=0); stock_minimo:int=Field(default=5,ge=0)
    stock_maximo:int|None=Field(None,ge=0); unidad_medida:str=Field(default='UNIDAD',max_length=30); fecha_vencimiento:date|None=None; imagen_url:str|None=None
    @model_validator(mode='after')
    def validar(self):
        if self.stock_maximo is not None and self.stock_maximo < self.stock_minimo: raise ValueError('El stock máximo no puede ser menor al stock mínimo')
        return self
class ProductoActualizar(BaseModel):
    categoria_id:uuid.UUID|None=None; proveedor_id:uuid.UUID|None=None; codigo_barras:str|None=None; nombre:str|None=None; marca:str|None=None; descripcion:str|None=None
    precio_compra:Decimal|None=Field(None,ge=0); precio_venta:Decimal|None=Field(None,gt=0); stock_minimo:int|None=Field(None,ge=0); stock_maximo:int|None=Field(None,ge=0)
    unidad_medida:str|None=None; fecha_vencimiento:date|None=None; imagen_url:str|None=None; estado:str|None=None
class ProductoResponse(BaseModel):
    id:uuid.UUID; categoria_id:uuid.UUID; categoria_nombre:str; proveedor_id:uuid.UUID|None; proveedor_nombre:str|None; codigo:str; codigo_barras:str|None; nombre:str; marca:str|None
    descripcion:str|None; precio_compra:Decimal; precio_venta:Decimal; stock:int; stock_minimo:int; stock_maximo:int|None; unidad_medida:str; fecha_vencimiento:date|None; imagen_url:str|None; estado:str; stock_bajo:bool

class AjusteInventarioRequest(BaseModel):
    producto_id:uuid.UUID; cantidad:int; tipo:str; motivo:str=Field(min_length=3,max_length=500)
    @field_validator('tipo')
    @classmethod
    def tipo_ok(cls,v):
        v=v.upper()
        if v not in ('ENTRADA','SALIDA','AJUSTE'): raise ValueError('Tipo inválido')
        return v
    @model_validator(mode='after')
    def cantidad_ok(self):
        if self.tipo in ('ENTRADA','SALIDA') and self.cantidad <= 0: raise ValueError('La cantidad debe ser mayor que cero')
        if self.tipo=='AJUSTE' and self.cantidad < 0: raise ValueError('El stock final no puede ser negativo')
        return self
class MovimientoResponse(BaseModel):
    id:uuid.UUID; producto_id:uuid.UUID; producto_nombre:str; tipo:str; cantidad:int; stock_resultante:int; motivo:str; usuario_id:uuid.UUID; fecha:datetime

class CompraDetalleCrear(BaseModel):
    producto_id:uuid.UUID; cantidad:int=Field(gt=0); costo_unitario:Decimal=Field(gt=0); descuento:Decimal=Field(default=Decimal('0'),ge=0)
class CompraCrear(BaseModel):
    proveedor_id:uuid.UUID; detalles:list[CompraDetalleCrear]=Field(min_length=1); descuento:Decimal=Field(default=Decimal('0'),ge=0); impuesto:Decimal=Field(default=Decimal('0'),ge=0); observaciones:str|None=None
class CompraDetalleResponse(BaseModel):
    producto_id:uuid.UUID; producto_nombre:str; cantidad:int; costo_unitario:Decimal; descuento:Decimal; subtotal:Decimal
class CompraResponse(BaseModel):
    id:uuid.UUID; numero_compra:str; proveedor_id:uuid.UUID; proveedor_nombre:str; usuario_id:uuid.UUID; subtotal:Decimal; descuento:Decimal; impuesto:Decimal; total:Decimal; estado:str; observaciones:str|None; fecha:datetime; detalles:list[CompraDetalleResponse]

class InventarioResumenResponse(BaseModel):
    total_productos:int; productos_activos:int; productos_agotados:int; productos_stock_bajo:int; valor_inventario:Decimal
