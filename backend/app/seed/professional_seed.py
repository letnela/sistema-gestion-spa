"""Reinicio seguro y carga profesional completa para entorno de demostración.

ADVERTENCIA: elimina todos los datos de negocio existentes, conserva el esquema
Alembic y vuelve a poblar el sistema con información coherente para todos los módulos.

Uso:
    python -m app.seed.professional_seed --confirm-reset
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.constants import (
    EstadoCita, EstadoComision, EstadoGenerico, EstadoPago, EstadoVenta,
    MetodoPago, RolesSistema, TipoComision, TipoMovimientoInventario,
)
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.appointment_model import Cita, CitaServicio
from app.models.cash_model import CajaMovimiento, CajaSesion
from app.models.client_model import Cliente
from app.models.commission_model import Comision
from app.models.employee_model import Empleado, EmpleadoServicio, HorarioEmpleado
from app.models.inventory_model import InventarioMovimiento
from app.models.payment_model import Pago
from app.models.product_model import CategoriaProducto, Producto
from app.models.promotion_model import Promocion, PromocionProducto, PromocionServicio
from app.models.purchase_model import Compra, CompraDetalle
from app.models.role_model import Rol
from app.models.sale_model import Venta, VentaDetalle
from app.models.salon_config_model import ConfiguracionSalon
from app.models.service_model import CategoriaServicio, Servicio
from app.models.supplier_model import Proveedor, ProveedorProducto
from app.models.user_model import Usuario
from app.seed.roles_seed import seed_roles

TABLES = [
    "intentos_login", "notificaciones", "auditoria", "pagos", "comisiones",
    "venta_detalles", "ventas", "caja_movimientos", "caja_sesiones",
    "compra_detalles", "compras", "inventario_movimientos", "promocion_productos",
    "promocion_servicios", "promociones", "cita_servicios", "citas",
    "bloqueos_horario", "vacaciones_empleado", "horarios_empleado", "empleado_servicio",
    "empleados", "proveedor_producto", "productos", "categorias_producto", "proveedores",
    "servicios", "categorias_servicio", "usuarios", "clientes", "configuracion_salon", "roles",
]


def reset_database(db: Session) -> None:
    joined = ", ".join(f'\"{name}\"' for name in TABLES)
    db.execute(text(f"TRUNCATE TABLE {joined} RESTART IDENTITY CASCADE"))
    db.commit()


def create_users(db: Session, roles: dict[str, Rol]) -> dict[str, Usuario]:
    data = [
        ("Administrador General", "admin@salon.com", "Admin123*", RolesSistema.ADMINISTRADOR, "999100001"),
        ("Valentina Rojas", "recepcion@salon.com", "Recepcion123*", RolesSistema.RECEPCIONISTA, "999100002"),
        ("Sofía Reyes", "estilista@salon.com", "Estilista123*", RolesSistema.ESTILISTA, "999100003"),
    ]
    result = {}
    for name, email, password, role, phone in data:
        user = Usuario(nombre_completo=name, correo=email, password_hash=hash_password(password),
                       rol_id=roles[role].id, estado=EstadoGenerico.ACTIVO, telefono=phone,
                       debe_cambiar_password=False)
        db.add(user); db.flush(); result[email] = user
    db.commit(); return result


def create_clients(db: Session, roles: dict[str, Rol]) -> list[Cliente]:
    people = [
        ("Camila", "Torres Salazar", "70451231", "987410201", "camila.torres@demo.pe", "Miraflores", "Cabello ondulado; prefiere productos sin sulfatos", "Sensibilidad leve al amoniaco"),
        ("Luciana", "Mendoza Paredes", "71562342", "987410202", "luciana.mendoza@demo.pe", "San Isidro", "Tonos cálidos y manicure nude", None),
        ("Mariana", "Vega Castillo", "72673453", "987410203", "mariana.vega@demo.pe", "Surco", "Tratamientos hidratantes mensuales", "Piel sensible"),
        ("Andrea", "Gómez Rivas", "73784564", "987410204", "andrea.gomez@demo.pe", "Barranco", "Balayage natural y ondas", None),
        ("Valeria", "Ponce Herrera", "74895675", "987410205", "valeria.ponce@demo.pe", "La Molina", "Manicure gel y diseño minimalista", "Alergia al látex"),
        ("Daniela", "Soto Aguilar", "75906786", "987410206", "daniela.soto@demo.pe", "Jesús María", "Cortes en capas", None),
        ("Paola", "Núñez Cabrera", "76017897", "987410207", "paola.nunez@demo.pe", "Magdalena", "Spa facial cada 6 semanas", "Rosácea; evitar exfoliantes fuertes"),
        ("Fernanda", "Luna Campos", "77128908", "987410208", "fernanda.luna@demo.pe", "Pueblo Libre", "Alisado y nutrición capilar", None),
        ("Gabriela", "Ramos Peña", "78239019", "987410209", "gabriela.ramos@demo.pe", "San Miguel", "Coloración sin decoloración", "Sensibilidad al peróxido alto"),
        ("Alejandra", "Cruz Medina", "79340120", "987410210", "alejandra.cruz@demo.pe", "Lince", "Pedicure spa", None),
        ("Carlos", "Ramírez Torres", "45678913", "987654322", "carlos.ramirez@demo.pe", "San Borja", "Corte ejecutivo cada 3 semanas", None),
        ("Diego", "Fernández Silva", "45678915", "987654324", "diego.fernandez@demo.pe", "Surquillo", "Barba y corte clásico", None),
        ("Mateo", "Chávez León", "80451231", "987410213", "mateo.chavez@demo.pe", "Breña", "Fade bajo", None),
        ("Sebastián", "Ortiz Flores", "81562342", "987410214", "sebastian.ortiz@demo.pe", "Chorrillos", "Corte texturizado", None),
        ("Renata", "Alva Morales", "82673453", "987410215", "renata.alva@demo.pe", "San Isidro", "Novia; pruebas de peinado", None),
    ]
    clients=[]
    for i,(first,last,doc,phone,email,district,prefs,allergy) in enumerate(people):
        client=Cliente(nombres=first,apellidos=last,documento=doc,telefono=phone,correo=email,
                       direccion=f"{district}, Lima",fecha_nacimiento=date(1988+i%12, (i%12)+1, min(10+i,28)),
                       preferencias=prefs,alergias=allergy,observaciones="Cliente demo profesional",
                       estado=EstadoGenerico.ACTIVO)
        db.add(client); db.flush(); clients.append(client)
        if i < 12:
            user=Usuario(nombre_completo=f"{first} {last}",correo=email,password_hash=hash_password("Cliente123*"),
                         rol_id=roles[RolesSistema.CLIENTE].id,cliente_id=client.id,telefono=phone,
                         estado=EstadoGenerico.ACTIVO,debe_cambiar_password=False)
            db.add(user)
    db.commit(); return clients



SERVICE_IMAGES = [
 "https://images.unsplash.com/photo-1560066984-138dadb4c035?auto=format&fit=crop&w=1200&q=82",
 "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=1200&q=82",
 "https://images.unsplash.com/photo-1604654894610-df63bc536371?auto=format&fit=crop&w=1200&q=82",
 "https://images.unsplash.com/photo-1621605815971-fbc98d665033?auto=format&fit=crop&w=1200&q=82",
 "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?auto=format&fit=crop&w=1200&q=82",
 "https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?auto=format&fit=crop&w=1200&q=82",
]
PRODUCT_IMAGES = [
 "https://images.unsplash.com/photo-1522338242992-e1a54906a8da?auto=format&fit=crop&w=1000&q=82",
 "https://images.unsplash.com/photo-1631214524020-7e18db9a8f92?auto=format&fit=crop&w=1000&q=82",
 "https://images.unsplash.com/photo-1604654894610-df63bc536371?auto=format&fit=crop&w=1000&q=82",
 "https://images.unsplash.com/photo-1621605815971-fbc98d665033?auto=format&fit=crop&w=1000&q=82",
 "https://images.unsplash.com/photo-1556229010-6c3f2c9ca5f8?auto=format&fit=crop&w=1000&q=82",
 "https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?auto=format&fit=crop&w=1000&q=82",
]

def create_services(db: Session) -> tuple[list[CategoriaServicio], list[Servicio]]:
    cats=[]
    for n,d in [
        ("Cabello","Corte, styling y tratamientos capilares"),("Coloración","Técnicas de color profesional"),
        ("Uñas","Manicure, pedicure y nail art"),("Barbería","Corte masculino y cuidado de barba"),
        ("Spa & Facial","Bienestar, limpieza y cuidado facial"),("Novias & Eventos","Peinado y maquillaje para ocasiones especiales")]:
        c=CategoriaServicio(nombre=n,descripcion=d,estado="ACTIVO"); db.add(c); db.flush(); cats.append(c)
    rows=[
        (0,"Corte Dama Premium","Diagnóstico, lavado, corte y brushing",65,60,12),(0,"Brushing & Ondas","Lavado y styling de larga duración",50,45,10),(0,"Tratamiento Repair Luxe","Reparación profunda para cabello dañado",95,75,12),(0,"Alisado Orgánico","Alisado progresivo libre de formol",280,180,15),
        (1,"Color Global","Coloración completa con diagnóstico",180,150,15),(1,"Balayage Signature","Técnica personalizada con matización",360,240,18),(1,"Retoque de Raíz","Cobertura profesional hasta 3 cm",110,90,14),(1,"Baño de Color","Refrescamiento de tono y brillo",130,90,14),
        (2,"Manicure Gel","Preparación, esmaltado gel y acabado",55,60,10),(2,"Pedicure Spa","Exfoliación, hidratación y esmaltado",70,75,10),(2,"Nail Art Minimalista","Diseño por set",35,30,10),(2,"Retiro de Gel","Retiro seguro y cuidado de uña",25,30,8),
        (3,"Corte Ejecutivo","Corte masculino y styling",45,45,10),(3,"Fade & Diseño","Degradado técnico y terminación",55,60,12),(3,"Perfilado de Barba","Toalla caliente, perfilado e hidratación",35,35,10),
        (4,"Limpieza Facial Profunda","Evaluación, extracción e hidratación",120,90,12),(4,"Hydra Glow","Hidratación intensiva y luminosidad",145,90,12),(4,"Masaje Relajante 60 min","Masaje corporal de relajación",150,60,12),
        (5,"Peinado Social","Peinado profesional para evento",110,90,15),(5,"Maquillaje Social","Maquillaje de larga duración",140,90,15),(5,"Pack Novia Premium","Prueba, maquillaje y peinado",650,300,18),
    ]
    services=[]
    for cat_idx,n,d,p,mins,commission in rows:
        s=Servicio(categoria_id=cats[cat_idx].id,nombre=n,descripcion=d,precio=Decimal(str(p)),
                   duracion_minutos=mins,porcentaje_comision=Decimal(str(commission)),imagen_url=SERVICE_IMAGES[cat_idx],estado="ACTIVO")
        db.add(s); services.append(s)
    db.commit(); return cats,services


def create_employees(db: Session, users: dict[str,Usuario], services:list[Servicio]) -> list[Empleado]:
    people=[
        ("Sofía","Reyes Quispe","ESTILISTA SENIOR","Coloración, balayage y corte dama",2200,15,users["estilista@salon.com"]),
        ("Martina","Salazar Núñez","COLORISTA","Color global, raíz y tratamientos",2000,14,None),
        ("Valeria","Chávez Ibáñez","NAIL ARTIST","Manicure, pedicure y nail art",1850,12,None),
        ("Diego","Huamán Rojas","BARBERO","Corte masculino, fade y barba",1900,12,None),
        ("Paula","Vargas León","ESTETICISTA","Faciales, masajes y maquillaje",2100,14,None),
    ]
    emps=[]
    for i,(f,l,cargo,spec,salary,comm,user) in enumerate(people):
        e=Empleado(usuario_id=user.id if user else None,nombres=f,apellidos=l,documento=f"9000000{i+1}",
                   telefono=f"98650010{i}",correo=f"{f.lower()}.{l.split()[0].lower()}@salon.com",cargo=cargo,
                   especialidad=spec,salario=Decimal(str(salary)),porcentaje_comision_default=Decimal(str(comm)),
                   fecha_ingreso=date.today()-timedelta(days=400-i*45),estado="ACTIVO")
        db.add(e); db.flush(); emps.append(e)
        for day in range(1,7):
            db.add(HorarioEmpleado(empleado_id=e.id,dia_semana=day,hora_entrada=time(9),hora_salida=time(19),
                                   hora_inicio_descanso=time(13),hora_fin_descanso=time(14),es_dia_libre=False))
        db.add(HorarioEmpleado(empleado_id=e.id,dia_semana=7,hora_entrada=time(9),hora_salida=time(9),es_dia_libre=True))
    assignment={0:[0,1,2,3,4,5,6,7,18,20],1:[2,4,5,6,7],2:[8,9,10,11],3:[12,13,14],4:[15,16,17,19,20]}
    for ei, sis in assignment.items():
        for si in sis: db.add(EmpleadoServicio(empleado_id=emps[ei].id,servicio_id=services[si].id))
    db.commit(); return emps


def create_inventory(db:Session, admin:Usuario) -> tuple[list[Proveedor],list[Producto]]:
    supplier_rows=[
        ("L'Oréal Professionnel Perú SAC","20512345001","Andrea Villar","ventas.pro@loreal-demo.pe","Av. Javier Prado 1234, San Isidro"),
        ("Wella Professionals Distribución","20512345002","Renzo Paz","pedidos@wella-demo.pe","Av. República de Panamá 4580, Surquillo"),
        ("Beauty Supply Perú EIRL","20512345003","Mónica Silva","corporativo@beautysupply-demo.pe","Jr. Puno 450, Cercado de Lima"),
        ("OPI & Nail Pro Import SAC","20512345004","Carla Núñez","ventas@nailpro-demo.pe","Av. La Marina 2340, San Miguel"),
        ("Barber House Wholesale SAC","20512345005","Luis Rojas","mayoristas@barberhouse-demo.pe","Av. Canadá 1670, La Victoria"),
    ]
    suppliers=[]
    for i,(name,ruc,contact,email,address) in enumerate(supplier_rows):
        p=Proveedor(razon_social=name,documento_ruc=ruc,contacto_nombre=contact,correo=email,
                    telefono=f"01-640-20{i+1}0",direccion=address,estado="ACTIVO")
        db.add(p); db.flush(); suppliers.append(p)
    cat_rows=[("Cuidado Capilar","Shampoo, mascarillas, tratamientos y styling"),("Color Profesional","Tintes, oxidantes, decolorantes y matizadores"),("Nail Studio","Esmaltes, bases, geles y herramientas de uñas"),("Barbería","Productos y accesorios para barbería"),("Skin & Spa","Productos faciales, corporales y de cabina"),("Herramientas Eléctricas","Equipos profesionales de styling")]
    cats=[]
    for n,d in cat_rows:
        c=CategoriaProducto(nombre=n,descripcion=d,estado="ACTIVO");db.add(c);db.flush();cats.append(c)
    rows=[
        (0,"CAP-001","Absolut Repair Shampoo 500ml","L'Oréal Professionnel",68,105,24,8,40),(0,"CAP-002","Absolut Repair Mask 250ml","L'Oréal Professionnel",72,118,18,6,30),(0,"CAP-003","Metal Detox Oil 50ml","L'Oréal Professionnel",78,129,12,4,20),(0,"CAP-004","Nutri-Enrich Conditioner 500ml","Wella Professionals",64,99,20,6,35),(0,"CAP-005","EIMI Thermal Image 150ml","Wella Professionals",42,72,28,8,45),(0,"CAP-006","Moroccanoil Treatment 100ml","Moroccanoil",95,155,10,4,18),
        (1,"COL-001","Koleston Perfect 60ml - 7/0","Wella Professionals",24,42,36,10,60),(1,"COL-002","Koleston Perfect 60ml - 8/1","Wella Professionals",24,42,32,10,60),(1,"COL-003","Blondor Multi Blonde 800g","Wella Professionals",115,185,14,4,25),(1,"COL-004","Oxidante Welloxon 20 Vol 1L","Wella Professionals",38,65,20,6,35),(1,"COL-005","Oxidante Welloxon 30 Vol 1L","Wella Professionals",38,65,16,6,30),(1,"COL-006","Dia Light 50ml - 9.01","L'Oréal Professionnel",27,48,22,8,40),
        (2,"NAI-001","GelColor Bubble Bath 15ml","OPI",38,65,18,6,30),(2,"NAI-002","GelColor Big Apple Red 15ml","OPI",38,65,16,6,30),(2,"NAI-003","Base Coat Rubber 15ml","Nail Pro",25,45,20,6,35),(2,"NAI-004","Top Coat No Wipe 15ml","Nail Pro",26,48,22,6,35),(2,"NAI-005","Aceite de Cutícula 30ml","Cuccio",18,35,25,8,40),
        (3,"BAR-001","Pomada Matte 100g","Reuzel",42,75,20,6,35),(3,"BAR-002","Aceite para Barba 50ml","Proraso",36,65,15,5,25),(3,"BAR-003","Shaving Cream 150ml","Proraso",31,55,16,5,28),(3,"BAR-004","Navajas Derby Premium x100","Derby",28,49,10,4,20),
        (4,"SPA-001","Gel Limpiador Profesional 500ml","Dermalogica",95,160,8,3,15),(4,"SPA-002","Mascarilla Hydra Glow 250ml","Dermalogica",110,185,7,3,14),(4,"SPA-003","Protector Solar SPF50 50ml","La Roche-Posay",48,82,14,5,25),(4,"SPA-004","Aceite de Masaje Lavanda 1L","Spa Essentials",45,78,9,3,18),
        (5,"HER-001","Secadora Rapido 2200W","BaBylissPRO",420,649,4,2,8),(5,"HER-002","Plancha Nano Titanium","BaBylissPRO",380,599,5,2,8),(5,"HER-003","Máquina Magic Clip Cordless","Wahl",390,620,4,2,8),(5,"HER-004","Lámpara UV/LED 48W","SUN",95,165,6,2,10),(5,"HER-005","Cepillo Térmico 45mm","Olivia Garden",58,98,12,4,20),
    ]
    products=[]
    for idx,(ci,code,name,brand,buy,sell,stock,min_s,max_s) in enumerate(rows):
        p=Producto(categoria_id=cats[ci].id,proveedor_id=suppliers[idx%len(suppliers)].id,codigo=code,
                   codigo_barras=f"775{100000000+idx}",nombre=name,marca=brand,
                   descripcion=f"Producto profesional {brand} para uso y venta en salón.",precio_compra=Decimal(str(buy)),
                   precio_venta=Decimal(str(sell)),stock=stock,stock_minimo=min_s,stock_maximo=max_s,
                   unidad_medida="UNIDAD",imagen_url=PRODUCT_IMAGES[ci],estado="ACTIVO")
        db.add(p);db.flush();products.append(p)
        db.add(ProveedorProducto(proveedor_id=p.proveedor_id,producto_id=p.id))
        db.add(InventarioMovimiento(producto_id=p.id,tipo=TipoMovimientoInventario.ENTRADA,cantidad=stock,
                                    stock_resultante=stock,motivo="Inventario inicial profesional Fase 19",usuario_id=admin.id))
    db.commit(); return suppliers,products


def create_operations(db:Session, clients:list[Cliente], emps:list[Empleado], services:list[Servicio], products:list[Producto], suppliers:list[Proveedor], users:dict[str,Usuario]) -> None:
    today=date.today(); reception=users["recepcion@salon.com"]; admin=users["admin@salon.com"]
    appointments=[]
    states=[EstadoCita.FINALIZADA,EstadoCita.FINALIZADA,EstadoCita.CONFIRMADA,EstadoCita.PENDIENTE,EstadoCita.CANCELADA,EstadoCita.NO_ASISTIO]
    for i in range(60):
        service=services[i%len(services)]; emp=emps[i%len(emps)]; day=today+timedelta(days=(i%31)-15)
        start=time(9+(i%8), 0 if i%2==0 else 30); start_dt=datetime.combine(day,start); end_dt=start_dt+timedelta(minutes=service.duracion_minutos)
        state=states[i%len(states)] if day<=today else (EstadoCita.CONFIRMADA if i%2==0 else EstadoCita.PENDIENTE)
        a=Cita(cliente_id=clients[i%len(clients)].id,empleado_id=emp.id,fecha=day,hora_inicio=start,
               hora_fin=end_dt.time(),duracion_total_minutos=service.duracion_minutos,precio_total=service.precio,
               estado=state,notas="Atención demo profesional",created_by=reception.id,updated_by=reception.id)
        if state==EstadoCita.CANCELADA: a.motivo_cancelacion="Reprogramación solicitada por el cliente"
        db.add(a);db.flush();db.add(CitaServicio(cita_id=a.id,servicio_id=service.id,precio_aplicado=service.precio,duracion_aplicada_minutos=service.duracion_minutos));appointments.append(a)
    db.commit()

    cash=CajaSesion(usuario_apertura_id=reception.id,fecha_apertura=datetime.now(timezone.utc)-timedelta(hours=6),
                    monto_apertura=Decimal("300.00"),estado="ABIERTA",observaciones="Turno principal de recepción")
    db.add(cash);db.flush()
    completed=[a for a in appointments if a.estado==EstadoCita.FINALIZADA]
    for i,a in enumerate(completed):
        service=services[i%len(services)]; product=products[i%len(products)]; include_product=i%2==0
        service_sub=service.precio; product_sub=product.precio_venta if include_product else Decimal("0")
        subtotal=service_sub+product_sub; discount=Decimal("10.00") if i==1 else Decimal("0"); taxable=subtotal-discount; tax=(taxable*Decimal("0.18")).quantize(Decimal("0.01")); total=taxable+tax
        v=Venta(numero_comprobante=f"B001-{i+1:08d}",cliente_id=a.cliente_id,cita_id=a.id,usuario_id=reception.id,
                subtotal=subtotal,descuento=discount,impuesto=tax,total=total,estado=EstadoVenta.COMPLETADA,
                fecha=datetime.now(timezone.utc)-timedelta(days=i),created_by=reception.id,updated_by=reception.id)
        db.add(v);db.flush();
        db.add(VentaDetalle(venta_id=v.id,servicio_id=service.id,empleado_id=a.empleado_id,cantidad=1,precio_unitario=service.precio,descuento=Decimal("0"),subtotal=service_sub))
        if include_product:
            db.add(VentaDetalle(venta_id=v.id,producto_id=product.id,cantidad=1,precio_unitario=product.precio_venta,descuento=Decimal("0"),subtotal=product_sub))
            product.stock-=1
            db.add(InventarioMovimiento(producto_id=product.id,tipo=TipoMovimientoInventario.SALIDA,cantidad=1,stock_resultante=product.stock,motivo=f"Venta {v.numero_comprobante}",usuario_id=reception.id))
        method=[MetodoPago.EFECTIVO,MetodoPago.TARJETA,MetodoPago.YAPE,MetodoPago.PLIN][i%4]
        db.add(Pago(venta_id=v.id,usuario_id=reception.id,monto=total,metodo=method,referencia=None if method==MetodoPago.EFECTIVO else f"OP-{i+1:06d}",estado=EstadoPago.COMPLETO,fecha=v.fecha))
        db.add(CajaMovimiento(caja_sesion_id=cash.id,usuario_id=reception.id,tipo="INGRESO",concepto=f"Venta {v.numero_comprobante}",monto=total,referencia=v.numero_comprobante,fecha=v.fecha))
        pct=service.porcentaje_comision; amount=(service.precio*pct/Decimal("100")).quantize(Decimal("0.01"))
        db.add(Comision(empleado_id=a.empleado_id,venta_id=v.id,tipo=TipoComision.SERVICIO,monto_base=service.precio,porcentaje_aplicado=pct,monto_comision=amount,estado=EstadoComision.PENDIENTE,periodo=today.replace(day=1),fecha=v.fecha))
    db.commit()

    for i in range(6):
        selected=products[(i*4)%len(products):((i*4)%len(products))+4]; subtotal=sum((p.precio_compra*Decimal("5") for p in selected),Decimal("0")); tax=(subtotal*Decimal("0.18")).quantize(Decimal("0.01"));
        purchase=Compra(numero_compra=f"OC-2026-{i+1:04d}",proveedor_id=suppliers[i%len(suppliers)].id,usuario_id=admin.id,subtotal=subtotal,descuento=Decimal("0"),impuesto=tax,total=subtotal+tax,estado="RECIBIDA",observaciones="Reposición planificada de inventario",fecha=datetime.now(timezone.utc)-timedelta(days=10-i*3))
        db.add(purchase);db.flush()
        for p in selected:
            db.add(CompraDetalle(compra_id=purchase.id,producto_id=p.id,cantidad=5,costo_unitario=p.precio_compra,descuento=Decimal("0"),subtotal=p.precio_compra*5))
    db.commit()


def create_promotions_and_config(db:Session, services:list[Servicio], products:list[Producto]) -> None:
    today=date.today()
    promos=[("Color Week",15,"15% en servicios seleccionados de color",[services[4],services[6]],[]),
            ("Glow Experience",20,"Experiencia facial premium",[services[16]],[]),
            ("Home Care Club",10,"Descuento en cuidado capilar para clientes del portal",[],products[:4])]
    for name,pct,desc,ss,ps in promos:
        promo=Promocion(nombre=name,descripcion=desc,porcentaje_descuento=Decimal(str(pct)),fecha_inicio=today-timedelta(days=3),fecha_fin=today+timedelta(days=30),activa=True)
        db.add(promo);db.flush()
        for s in ss: db.add(PromocionServicio(promocion_id=promo.id,servicio_id=s.id))
        for p in ps: db.add(PromocionProducto(promocion_id=promo.id,producto_id=p.id))
    db.add(ConfiguracionSalon(nombre_salon="Éclat Beauty Studio",ruc="20612345678",direccion="Av. Conquistadores 845, San Isidro, Lima",telefono="01 705 8899",correo="hola@eclatbeauty.pe",moneda="PEN",impuesto_porcentaje=Decimal("18.00"),horario_general="Lunes a sábado de 9:00 a 19:00",color_principal="#7C3AED",texto_comprobante="Gracias por elegir Éclat Beauty Studio. Reserva tu próxima experiencia desde el portal."))
    db.commit()


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("--confirm-reset",action="store_true")
    args=parser.parse_args()
    if not args.confirm_reset:
        raise SystemExit("Operación cancelada. Usa --confirm-reset para confirmar que deseas borrar y recargar toda la data.")
    db=SessionLocal()
    try:
        print("1/8 Limpiando data anterior...");reset_database(db)
        print("2/8 Creando roles...");roles=seed_roles(db)
        print("3/8 Creando usuarios base...");users=create_users(db,roles)
        print("4/8 Creando clientes profesionales y cuentas de portal...");clients=create_clients(db,roles)
        print("5/8 Creando catálogo de servicios y equipo...");_,services=create_services(db);emps=create_employees(db,users,services)
        print("6/8 Creando proveedores, productos y kardex...");suppliers,products=create_inventory(db,users["admin@salon.com"])
        print("7/8 Creando agenda, ventas, caja, pagos, comisiones y compras...");create_operations(db,clients,emps,services,products,suppliers,users)
        print("8/8 Creando promociones y configuración...");create_promotions_and_config(db,services,products)
        print("\nCarga profesional completada correctamente.")
        print("Usuarios internos: admin@salon.com / Admin123* | recepcion@salon.com / Recepcion123* | estilista@salon.com / Estilista123*")
        print("Clientes portal (primeros 6): correo @demo.pe / Cliente123*")
    except Exception:
        db.rollback(); raise
    finally:
        db.close()

if __name__=="__main__": main()
