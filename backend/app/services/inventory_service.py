"""Lógica de negocio de inventario, proveedores y compras."""
import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload
from app.core.constants import AccionAuditoria, EstadoGenerico, TipoMovimientoInventario
from app.core.exceptions import ConflictException, InsufficientStockException, NotFoundException, ValidationException
from app.models.product_model import CategoriaProducto, Producto
from app.models.supplier_model import Proveedor
from app.models.inventory_model import InventarioMovimiento
from app.models.purchase_model import Compra, CompraDetalle
from app.services.audit_service import registrar_auditoria

class InventoryService:
    def __init__(self,db:Session): self.db=db
    def _cat(self,id):
        x=self.db.get(CategoriaProducto,id)
        if not x: raise NotFoundException('Categoría de producto no encontrada')
        return x
    def _prov(self,id):
        x=self.db.get(Proveedor,id)
        if not x: raise NotFoundException('Proveedor no encontrado')
        return x
    def _prod(self,id,lock=False):
        q=self.db.query(Producto).filter(Producto.id==id)
        if lock: q=q.with_for_update()
        x=q.first()
        if not x: raise NotFoundException('Producto no encontrado')
        return x
    def crear_categoria(self,d,actor):
        if self.db.query(CategoriaProducto).filter(func.lower(CategoriaProducto.nombre)==d.nombre.lower()).first(): raise ConflictException('Ya existe una categoría con ese nombre')
        x=CategoriaProducto(**d.model_dump()); self.db.add(x); registrar_auditoria(self.db,actor.id,AccionAuditoria.CREAR,'INVENTARIO','CategoriaProducto',str(x.id),valor_nuevo=d); self.db.commit(); self.db.refresh(x); return x
    def listar_categorias(self): return self.db.query(CategoriaProducto).order_by(CategoriaProducto.nombre).all()

    def actualizar_categoria(self,id,d,actor):
        x=self._cat(id); data=d.model_dump(exclude_unset=True)
        if data.get('nombre'):
            dup=self.db.query(CategoriaProducto).filter(func.lower(CategoriaProducto.nombre)==data['nombre'].lower(),CategoriaProducto.id!=id).first()
            if dup: raise ConflictException('Ya existe una categoría con ese nombre')
        antes={'nombre':x.nombre,'estado':x.estado}
        for k,v in data.items(): setattr(x,k,v)
        registrar_auditoria(self.db,actor.id,AccionAuditoria.EDITAR,'INVENTARIO','CategoriaProducto',str(x.id),antes,data)
        self.db.commit(); self.db.refresh(x); return x
    def eliminar_categoria(self,id,actor):
        x=self._cat(id)
        if self.db.query(Producto).filter(Producto.categoria_id==id).count(): raise ConflictException('No se puede eliminar una categoría que tiene productos')
        registrar_auditoria(self.db,actor.id,AccionAuditoria.ELIMINAR,'INVENTARIO','CategoriaProducto',str(x.id),valor_anterior={'nombre':x.nombre})
        self.db.delete(x); self.db.commit()
    def actualizar_proveedor(self,id,d,actor):
        x=self._prov(id); data=d.model_dump(exclude_unset=True,mode='json')
        if data.get('documento_ruc'):
            dup=self.db.query(Proveedor).filter(Proveedor.documento_ruc==data['documento_ruc'],Proveedor.id!=id).first()
            if dup: raise ConflictException('Ya existe un proveedor con ese documento')
        antes={'razon_social':x.razon_social,'estado':x.estado}
        for k,v in data.items(): setattr(x,k,v)
        registrar_auditoria(self.db,actor.id,AccionAuditoria.EDITAR,'INVENTARIO','Proveedor',str(x.id),antes,data)
        self.db.commit(); self.db.refresh(x); return x
    def eliminar_proveedor(self,id,actor):
        x=self._prov(id)
        if self.db.query(Compra).filter(Compra.proveedor_id==id).count(): raise ConflictException('No se puede eliminar un proveedor con compras registradas')
        for prod in self.db.query(Producto).filter(Producto.proveedor_id==id).all(): prod.proveedor_id=None
        registrar_auditoria(self.db,actor.id,AccionAuditoria.ELIMINAR,'INVENTARIO','Proveedor',str(x.id),valor_anterior={'razon_social':x.razon_social})
        self.db.delete(x); self.db.commit()
    def eliminar_producto(self,id,actor):
        x=self._prod(id)
        if x.detalles_venta or x.movimientos: 
            x.estado=EstadoGenerico.INACTIVO
            registrar_auditoria(self.db,actor.id,AccionAuditoria.ELIMINAR,'INVENTARIO','Producto',str(x.id),valor_anterior={'nombre':x.nombre},valor_nuevo={'estado':'INACTIVO'})
        else:
            registrar_auditoria(self.db,actor.id,AccionAuditoria.ELIMINAR,'INVENTARIO','Producto',str(x.id),valor_anterior={'nombre':x.nombre})
            self.db.delete(x)
        self.db.commit()

    def crear_proveedor(self,d,actor):
        if self.db.query(Proveedor).filter(Proveedor.documento_ruc==d.documento_ruc).first(): raise ConflictException('Ya existe un proveedor con ese documento')
        x=Proveedor(**d.model_dump(mode='json')); self.db.add(x); registrar_auditoria(self.db,actor.id,AccionAuditoria.CREAR,'INVENTARIO','Proveedor',str(x.id),valor_nuevo=d); self.db.commit(); self.db.refresh(x); return x
    def listar_proveedores(self,busqueda=None,estado=None):
        q=self.db.query(Proveedor)
        if busqueda: q=q.filter(or_(Proveedor.razon_social.ilike(f'%{busqueda}%'),Proveedor.documento_ruc.ilike(f'%{busqueda}%')))
        if estado: q=q.filter(Proveedor.estado==estado)
        return q.order_by(Proveedor.razon_social).all()
    def crear_producto(self,d,actor):
        self._cat(d.categoria_id)
        if d.proveedor_id: self._prov(d.proveedor_id)
        codigo=d.codigo or f'PRD-{uuid.uuid4().hex[:8].upper()}'
        if self.db.query(Producto).filter(Producto.codigo==codigo).first(): raise ConflictException('El código ya existe')
        if d.codigo_barras and self.db.query(Producto).filter(Producto.codigo_barras==d.codigo_barras).first(): raise ConflictException('El código de barras ya existe')
        data=d.model_dump(); data['codigo']=codigo
        # El catálogo solo registra la ficha. Las existencias ingresan por Compras
        # o por un ajuste de inventario auditado; nunca al crear el producto.
        data['stock']=0
        x=Producto(**data); self.db.add(x); self.db.flush()
        registrar_auditoria(self.db,actor.id,AccionAuditoria.CREAR,'INVENTARIO','Producto',str(x.id),valor_nuevo=d); self.db.commit(); self.db.refresh(x); return x
    def listar_productos(self,busqueda=None,categoria_id=None,proveedor_id=None,estado=None,stock_bajo=None,pagina=1,tamano=20):
        q=self.db.query(Producto).options(joinedload(Producto.categoria),joinedload(Producto.proveedor))
        if busqueda: q=q.filter(or_(Producto.nombre.ilike(f'%{busqueda}%'),Producto.codigo.ilike(f'%{busqueda}%'),Producto.codigo_barras.ilike(f'%{busqueda}%')))
        if categoria_id:q=q.filter(Producto.categoria_id==categoria_id)
        if proveedor_id:q=q.filter(Producto.proveedor_id==proveedor_id)
        if estado:q=q.filter(Producto.estado==estado)
        if stock_bajo is True:q=q.filter(Producto.stock<=Producto.stock_minimo)
        total=q.count(); return q.order_by(Producto.nombre).offset((pagina-1)*tamano).limit(tamano).all(),total
    def actualizar_producto(self,id,d,actor):
        x=self._prod(id); antes={'nombre':x.nombre,'precio_venta':str(x.precio_venta),'estado':x.estado}
        data=d.model_dump(exclude_unset=True)
        if 'categoria_id' in data:self._cat(data['categoria_id'])
        if data.get('proveedor_id'):self._prov(data['proveedor_id'])
        if data.get('codigo_barras'):
            dup=self.db.query(Producto).filter(Producto.codigo_barras==data['codigo_barras'],Producto.id!=id).first()
            if dup: raise ConflictException('El código de barras ya existe')
        for k,v in data.items(): setattr(x,k,v)
        if x.stock_maximo is not None and x.stock_maximo<x.stock_minimo: raise ValidationException('El stock máximo no puede ser menor al mínimo')
        registrar_auditoria(self.db,actor.id,AccionAuditoria.EDITAR,'INVENTARIO','Producto',str(x.id),antes,data); self.db.commit(); self.db.refresh(x); return x
    def ajustar(self,d,actor):
        x=self._prod(d.producto_id,True); anterior=x.stock
        if d.tipo=='ENTRADA': nuevo=anterior+d.cantidad; mov_cant=d.cantidad
        elif d.tipo=='SALIDA':
            if anterior<d.cantidad: raise InsufficientStockException(f'Stock disponible: {anterior}')
            nuevo=anterior-d.cantidad; mov_cant=d.cantidad
        else: nuevo=d.cantidad; mov_cant=nuevo-anterior
        x.stock=nuevo; m=InventarioMovimiento(producto_id=x.id,tipo=d.tipo,cantidad=mov_cant,stock_resultante=nuevo,motivo=d.motivo,usuario_id=actor.id); self.db.add(m)
        registrar_auditoria(self.db,actor.id,AccionAuditoria.EDITAR,'INVENTARIO','Producto',str(x.id),{'stock':anterior},{'stock':nuevo,'motivo':d.motivo}); self.db.commit(); self.db.refresh(m); return m
    def kardex(self,producto_id,pagina=1,tamano=50):
        self._prod(producto_id); q=self.db.query(InventarioMovimiento).filter(InventarioMovimiento.producto_id==producto_id); total=q.count(); return q.order_by(InventarioMovimiento.fecha.desc()).offset((pagina-1)*tamano).limit(tamano).all(),total
    def alertas(self): return self.db.query(Producto).options(joinedload(Producto.categoria),joinedload(Producto.proveedor)).filter(Producto.estado=='ACTIVO',Producto.stock<=Producto.stock_minimo).order_by(Producto.stock).all()
    def resumen(self):
        rows=self.db.query(Producto).all(); return {'total_productos':len(rows),'productos_activos':sum(x.estado=='ACTIVO' for x in rows),'productos_agotados':sum(x.stock==0 for x in rows),'productos_stock_bajo':sum(x.stock<=x.stock_minimo for x in rows),'valor_inventario':sum((x.precio_compra*x.stock for x in rows),Decimal('0'))}

class PurchaseService:
    def __init__(self,db): self.db=db; self.inv=InventoryService(db)
    def crear(self,d,actor):
        p=self.inv._prov(d.proveedor_id)
        if p.estado!='ACTIVO': raise ValidationException('El proveedor está inactivo')
        subtotal=Decimal('0'); c=Compra(numero_compra=f'COM-{uuid.uuid4().hex[:10].upper()}',proveedor_id=p.id,usuario_id=actor.id,descuento=d.descuento,impuesto=d.impuesto,observaciones=d.observaciones)
        self.db.add(c); self.db.flush()
        for item in d.detalles:
            prod=self.inv._prod(item.producto_id,True)
            if prod.proveedor_id and prod.proveedor_id != p.id:
                raise ValidationException(
                    f'El producto {prod.nombre} pertenece a otro proveedor. '
                    'Corrige el proveedor del producto antes de registrar la compra.'
                )
            if not prod.proveedor_id:
                prod.proveedor_id = p.id
            linea=(item.costo_unitario*item.cantidad)-item.descuento
            if linea<0: raise ValidationException('El descuento de una línea excede su importe')
            subtotal+=linea; self.db.add(CompraDetalle(compra_id=c.id,producto_id=prod.id,cantidad=item.cantidad,costo_unitario=item.costo_unitario,descuento=item.descuento,subtotal=linea))
            prod.stock+=item.cantidad; prod.precio_compra=item.costo_unitario
            self.db.add(InventarioMovimiento(producto_id=prod.id,tipo='ENTRADA',cantidad=item.cantidad,stock_resultante=prod.stock,motivo=f'COMPRA {c.numero_compra}',usuario_id=actor.id))
        c.subtotal=subtotal; c.total=subtotal-d.descuento+d.impuesto
        if c.total<0: raise ValidationException('El total no puede ser negativo')
        registrar_auditoria(self.db,actor.id,AccionAuditoria.CREAR,'INVENTARIO','Compra',str(c.id),valor_nuevo=d); self.db.commit(); return self.obtener(c.id)
    def obtener(self,id):
        x=self.db.query(Compra).options(joinedload(Compra.proveedor),joinedload(Compra.detalles).joinedload(CompraDetalle.producto)).filter(Compra.id==id).first()
        if not x: raise NotFoundException('Compra no encontrada')
        return x
    def listar(self,proveedor_id=None,fecha_desde=None,fecha_hasta=None,pagina=1,tamano=20):
        q=self.db.query(Compra).options(joinedload(Compra.proveedor),joinedload(Compra.detalles).joinedload(CompraDetalle.producto))
        if proveedor_id:q=q.filter(Compra.proveedor_id==proveedor_id)
        if fecha_desde:q=q.filter(func.date(Compra.fecha)>=fecha_desde)
        if fecha_hasta:q=q.filter(func.date(Compra.fecha)<=fecha_hasta)
        total=q.count(); return q.order_by(Compra.fecha.desc()).offset((pagina-1)*tamano).limit(tamano).all(),total
