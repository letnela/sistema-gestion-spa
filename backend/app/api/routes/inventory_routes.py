"""Rutas REST de la Fase 8: inventario, proveedores y compras."""
import uuid
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, get_db
from app.core.constants import RolesSistema
from app.core.permissions import require_roles
from app.models.user_model import Usuario
from app.schemas.common_schema import RespuestaExito, RespuestaPaginada, RespuestaMensaje
from app.schemas.inventory_schema import *
from app.services.inventory_service import InventoryService, PurchaseService

router=APIRouter(tags=['Inventario y Proveedores'])
admin_recep=Depends(require_roles(RolesSistema.ADMINISTRADOR,RolesSistema.RECEPCIONISTA))

def producto_response(x):
    return ProductoResponse(id=x.id,categoria_id=x.categoria_id,categoria_nombre=x.categoria.nombre,
        proveedor_id=x.proveedor_id,proveedor_nombre=x.proveedor.razon_social if x.proveedor else None,
        codigo=x.codigo,codigo_barras=x.codigo_barras,nombre=x.nombre,marca=x.marca,descripcion=x.descripcion,
        precio_compra=x.precio_compra,precio_venta=x.precio_venta,stock=x.stock,stock_minimo=x.stock_minimo,
        stock_maximo=x.stock_maximo,unidad_medida=x.unidad_medida,fecha_vencimiento=x.fecha_vencimiento,
        imagen_url=x.imagen_url,estado=x.estado,stock_bajo=x.stock<=x.stock_minimo)

def movimiento_response(x):
    return MovimientoResponse(id=x.id,producto_id=x.producto_id,producto_nombre=x.producto.nombre,
        tipo=x.tipo,cantidad=x.cantidad,stock_resultante=x.stock_resultante,motivo=x.motivo,usuario_id=x.usuario_id,fecha=x.fecha)

def compra_response(x):
    return CompraResponse(id=x.id,numero_compra=x.numero_compra,proveedor_id=x.proveedor_id,
        proveedor_nombre=x.proveedor.razon_social,usuario_id=x.usuario_id,subtotal=x.subtotal,descuento=x.descuento,
        impuesto=x.impuesto,total=x.total,estado=x.estado,observaciones=x.observaciones,fecha=x.fecha,
        detalles=[CompraDetalleResponse(producto_id=d.producto_id,producto_nombre=d.producto.nombre,
          cantidad=d.cantidad,costo_unitario=d.costo_unitario,descuento=d.descuento,subtotal=d.subtotal) for d in x.detalles])

@router.get('/product-categories',response_model=RespuestaExito[list[CategoriaProductoResponse]])
def categorias(db:Session=Depends(get_db),u:Usuario=Depends(get_current_user)):
    return RespuestaExito(data=InventoryService(db).listar_categorias())
@router.post('/product-categories',response_model=RespuestaExito[CategoriaProductoResponse],status_code=201,dependencies=[admin_recep])
def crear_categoria(d:CategoriaProductoCrear,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    return RespuestaExito(data=InventoryService(db).crear_categoria(d,actor),message='Categoría creada correctamente')

@router.put('/product-categories/{categoria_id}',response_model=RespuestaExito[CategoriaProductoResponse],dependencies=[admin_recep])
def actualizar_categoria(categoria_id:uuid.UUID,d:CategoriaProductoActualizar,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    return RespuestaExito(data=InventoryService(db).actualizar_categoria(categoria_id,d,actor),message='Categoría actualizada')
@router.delete('/product-categories/{categoria_id}',response_model=RespuestaMensaje,dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def eliminar_categoria(categoria_id:uuid.UUID,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    InventoryService(db).eliminar_categoria(categoria_id,actor); return RespuestaMensaje(message='Categoría eliminada')

@router.get('/suppliers',response_model=RespuestaExito[list[ProveedorResponse]])
def proveedores(busqueda:str|None=None,estado:str|None=None,db:Session=Depends(get_db),u:Usuario=Depends(get_current_user)):
    return RespuestaExito(data=InventoryService(db).listar_proveedores(busqueda,estado))
@router.post('/suppliers',response_model=RespuestaExito[ProveedorResponse],status_code=201,dependencies=[admin_recep])
def crear_proveedor(d:ProveedorCrear,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    return RespuestaExito(data=InventoryService(db).crear_proveedor(d,actor),message='Proveedor creado correctamente')

@router.put('/suppliers/{proveedor_id}',response_model=RespuestaExito[ProveedorResponse],dependencies=[admin_recep])
def actualizar_proveedor(proveedor_id:uuid.UUID,d:ProveedorActualizar,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    return RespuestaExito(data=InventoryService(db).actualizar_proveedor(proveedor_id,d,actor),message='Proveedor actualizado')
@router.delete('/suppliers/{proveedor_id}',response_model=RespuestaMensaje,dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def eliminar_proveedor(proveedor_id:uuid.UUID,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    InventoryService(db).eliminar_proveedor(proveedor_id,actor); return RespuestaMensaje(message='Proveedor eliminado')

@router.get('/products',response_model=RespuestaPaginada[ProductoResponse])
def productos(busqueda:str|None=None,categoria_id:uuid.UUID|None=None,proveedor_id:uuid.UUID|None=None,
    estado:str|None=None,stock_bajo:bool|None=None,pagina:int=Query(1,ge=1),tamano_pagina:int=Query(20,ge=1,le=100),
    db:Session=Depends(get_db),u:Usuario=Depends(get_current_user)):
    items,total=InventoryService(db).listar_productos(busqueda,categoria_id,proveedor_id,estado,stock_bajo,pagina,tamano_pagina)
    return RespuestaPaginada.crear([producto_response(x) for x in items],total,pagina,tamano_pagina)
@router.post('/products',response_model=RespuestaExito[ProductoResponse],status_code=201,dependencies=[admin_recep])
def crear_producto(d:ProductoCrear,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    return RespuestaExito(data=producto_response(InventoryService(db).crear_producto(d,actor)),message='Producto creado correctamente')
@router.patch('/products/{producto_id}',response_model=RespuestaExito[ProductoResponse],dependencies=[admin_recep])
def actualizar_producto(producto_id:uuid.UUID,d:ProductoActualizar,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    return RespuestaExito(data=producto_response(InventoryService(db).actualizar_producto(producto_id,d,actor)),message='Producto actualizado correctamente')

@router.delete('/products/{producto_id}',response_model=RespuestaMensaje,dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def eliminar_producto(producto_id:uuid.UUID,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    InventoryService(db).eliminar_producto(producto_id,actor); return RespuestaMensaje(message='Producto eliminado o inactivado correctamente')

@router.post('/inventory/adjustments',response_model=RespuestaExito[MovimientoResponse],status_code=201,dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def ajustar(d:AjusteInventarioRequest,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    x=InventoryService(db).ajustar(d,actor); x.producto=InventoryService(db)._prod(x.producto_id); return RespuestaExito(data=movimiento_response(x),message='Inventario ajustado correctamente')
@router.get('/inventory/kardex/{producto_id}',response_model=RespuestaPaginada[MovimientoResponse])
def kardex(producto_id:uuid.UUID,pagina:int=Query(1,ge=1),tamano_pagina:int=Query(50,ge=1,le=100),db:Session=Depends(get_db),u:Usuario=Depends(get_current_user)):
    items,total=InventoryService(db).kardex(producto_id,pagina,tamano_pagina); return RespuestaPaginada.crear([movimiento_response(x) for x in items],total,pagina,tamano_pagina)
@router.get('/inventory/alerts',response_model=RespuestaExito[list[ProductoResponse]])
def alertas(db:Session=Depends(get_db),u:Usuario=Depends(get_current_user)):
    return RespuestaExito(data=[producto_response(x) for x in InventoryService(db).alertas()])
@router.get('/inventory/summary',response_model=RespuestaExito[InventarioResumenResponse])
def resumen(db:Session=Depends(get_db),u:Usuario=Depends(get_current_user)):
    return RespuestaExito(data=InventoryService(db).resumen())

@router.post('/purchases',response_model=RespuestaExito[CompraResponse],status_code=201,dependencies=[admin_recep])
def crear_compra(d:CompraCrear,actor:Usuario=Depends(get_current_user),db:Session=Depends(get_db)):
    return RespuestaExito(data=compra_response(PurchaseService(db).crear(d,actor)),message='Compra registrada correctamente')
@router.get('/purchases',response_model=RespuestaPaginada[CompraResponse])
def compras(proveedor_id:uuid.UUID|None=None,fecha_desde:date|None=None,fecha_hasta:date|None=None,pagina:int=Query(1,ge=1),tamano_pagina:int=Query(20,ge=1,le=100),db:Session=Depends(get_db),u:Usuario=Depends(get_current_user)):
    items,total=PurchaseService(db).listar(proveedor_id,fecha_desde,fecha_hasta,pagina,tamano_pagina); return RespuestaPaginada.crear([compra_response(x) for x in items],total,pagina,tamano_pagina)
@router.get('/purchases/{compra_id}',response_model=RespuestaExito[CompraResponse])
def obtener_compra(compra_id:uuid.UUID,db:Session=Depends(get_db),u:Usuario=Depends(get_current_user)):
    return RespuestaExito(data=compra_response(PurchaseService(db).obtener(compra_id)))
