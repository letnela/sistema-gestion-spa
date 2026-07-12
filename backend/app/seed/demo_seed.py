"""
Seed de datos de demostración para poblar el sistema con información de ejemplo.
Cubre: clientes, empleados, categorías y servicios, categorías y productos,
proveedores, horarios de empleados y promociones.

NOTA: los datos de ejemplo de citas y ventas se generan en fases posteriores
(Fase 3 y Fase 5), una vez implementados los servicios de aplicación que
garantizan las reglas de negocio (evitar doble reserva, descuento de stock, etc.).
Generar esos registros directamente aquí, sin pasar por esa validación,
podría dejar la base de datos en un estado inconsistente.
"""
from datetime import date, time, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.constants import EstadoGenerico
from app.models.client_model import Cliente
from app.models.employee_model import Empleado, EmpleadoServicio, HorarioEmpleado
from app.models.product_model import CategoriaProducto, Producto
from app.models.promotion_model import Promocion, PromocionServicio
from app.models.salon_config_model import ConfiguracionSalon
from app.models.service_model import CategoriaServicio, Servicio
from app.models.supplier_model import Proveedor
from app.models.user_model import Usuario


def seed_clientes(db: Session) -> list[Cliente]:
    """Crea 5 clientes de ejemplo si la tabla está vacía."""
    if db.query(Cliente).count() > 0:
        return db.query(Cliente).all()

    datos_clientes = [
        {"nombres": "María", "apellidos": "González Pérez", "documento": "45678912",
         "telefono": "987654321", "correo": "maria.gonzalez@example.com", "alergias": "Ninguna conocida"},
        {"nombres": "Carlos", "apellidos": "Ramírez Torres", "documento": "45678913",
         "telefono": "987654322", "correo": "carlos.ramirez@example.com", "alergias": None},
        {"nombres": "Ana", "apellidos": "López Vargas", "documento": "45678914",
         "telefono": "987654323", "correo": "ana.lopez@example.com", "alergias": "Alergia al amoniaco"},
        {"nombres": "Jorge", "apellidos": "Fernández Silva", "documento": "45678915",
         "telefono": "987654324", "correo": "jorge.fernandez@example.com", "alergias": None},
        {"nombres": "Lucía", "apellidos": "Mendoza Castro", "documento": "45678916",
         "telefono": "987654325", "correo": "lucia.mendoza@example.com", "alergias": "Piel sensible"},
    ]

    clientes: list[Cliente] = []
    for datos in datos_clientes:
        cliente = Cliente(
            nombres=datos["nombres"],
            apellidos=datos["apellidos"],
            documento=datos["documento"],
            telefono=datos["telefono"],
            correo=datos["correo"],
            alergias=datos["alergias"],
            estado=EstadoGenerico.ACTIVO,
        )
        db.add(cliente)
        clientes.append(cliente)

    db.flush()
    db.commit()
    return clientes


def seed_categorias_y_servicios(db: Session) -> list[Servicio]:
    """Crea categorías y 8 servicios de ejemplo si la tabla está vacía."""
    if db.query(Servicio).count() > 0:
        return db.query(Servicio).all()

    cat_cabello = CategoriaServicio(nombre="Cabello", descripcion="Servicios relacionados al cabello")
    cat_unas = CategoriaServicio(nombre="Uñas", descripcion="Manicure y pedicure")
    cat_spa = CategoriaServicio(nombre="Spa Facial", descripcion="Tratamientos faciales y de relajación")
    db.add_all([cat_cabello, cat_unas, cat_spa])
    db.flush()

    servicios_data = [
        {"categoria": cat_cabello, "nombre": "Corte de Cabello Dama", "precio": Decimal("35.00"), "duracion": 45},
        {"categoria": cat_cabello, "nombre": "Corte de Cabello Caballero", "precio": Decimal("25.00"), "duracion": 30},
        {"categoria": cat_cabello, "nombre": "Coloración Completa", "precio": Decimal("120.00"), "duracion": 120},
        {"categoria": cat_cabello, "nombre": "Peinado para Evento", "precio": Decimal("60.00"), "duracion": 60},
        {"categoria": cat_unas, "nombre": "Manicure Clásico", "precio": Decimal("20.00"), "duracion": 40},
        {"categoria": cat_unas, "nombre": "Pedicure Spa", "precio": Decimal("30.00"), "duracion": 50},
        {"categoria": cat_spa, "nombre": "Limpieza Facial Profunda", "precio": Decimal("80.00"), "duracion": 60},
        {"categoria": cat_spa, "nombre": "Masaje Relajante", "precio": Decimal("70.00"), "duracion": 50},
    ]

    servicios: list[Servicio] = []
    for datos in servicios_data:
        servicio = Servicio(
            categoria_id=datos["categoria"].id,
            nombre=datos["nombre"],
            precio=datos["precio"],
            duracion_minutos=datos["duracion"],
            porcentaje_comision=Decimal("10.00"),
            estado=EstadoGenerico.ACTIVO,
        )
        db.add(servicio)
        servicios.append(servicio)

    db.flush()
    db.commit()
    return servicios


def seed_empleados(db: Session, servicios: list[Servicio]) -> list[Empleado]:
    """Crea 3 empleados de ejemplo, sus horarios y sus servicios asignados."""
    if db.query(Empleado).count() > 0:
        return db.query(Empleado).all()

    usuario_estilista = db.query(Usuario).filter(Usuario.correo == "estilista@salon.com").first()

    datos_empleados = [
        {
            "nombres": "Sofía", "apellidos": "Reyes Quispe", "cargo": "ESTILISTA",
            "especialidad": "Coloración y cortes de dama", "usuario": usuario_estilista,
        },
        {
            "nombres": "Diego", "apellidos": "Huamán Rojas", "cargo": "ESTILISTA",
            "especialidad": "Cortes de caballero y barbería", "usuario": None,
        },
        {
            "nombres": "Valeria", "apellidos": "Chávez Ibáñez", "cargo": "ESTILISTA",
            "especialidad": "Manicure, pedicure y spa facial", "usuario": None,
        },
    ]

    empleados: list[Empleado] = []
    for datos in datos_empleados:
        empleado = Empleado(
            usuario_id=datos["usuario"].id if datos["usuario"] else None,
            nombres=datos["nombres"],
            apellidos=datos["apellidos"],
            cargo=datos["cargo"],
            especialidad=datos["especialidad"],
            porcentaje_comision_default=Decimal("10.00"),
            fecha_ingreso=date.today() - timedelta(days=365),
            estado=EstadoGenerico.ACTIVO,
        )
        db.add(empleado)
        db.flush()

        # Horario estándar de lunes (1) a sábado (6), 9:00 a 18:00 con descanso 13:00-14:00
        for dia in range(1, 7):
            db.add(
                HorarioEmpleado(
                    empleado_id=empleado.id,
                    dia_semana=dia,
                    hora_entrada=time(9, 0),
                    hora_salida=time(18, 0),
                    hora_inicio_descanso=time(13, 0),
                    hora_fin_descanso=time(14, 0),
                    es_dia_libre=False,
                )
            )
        db.add(
            HorarioEmpleado(
                empleado_id=empleado.id, dia_semana=7,
                hora_entrada=time(9, 0), hora_salida=time(9, 0), es_dia_libre=True,
            )
        )
        empleados.append(empleado)

    db.flush()

    # Asignación de servicios: cada empleado puede realizar servicios afines a su especialidad
    if len(empleados) == 3 and len(servicios) == 8:
        asignaciones = {
            empleados[0]: [servicios[0], servicios[2], servicios[3]],  # Sofía: dama, color, peinado
            empleados[1]: [servicios[1]],  # Diego: caballero
            empleados[2]: [servicios[4], servicios[5], servicios[6], servicios[7]],  # Valeria: uñas y spa
        }
        for empleado, lista_servicios in asignaciones.items():
            for servicio in lista_servicios:
                db.add(EmpleadoServicio(empleado_id=empleado.id, servicio_id=servicio.id))

    db.commit()
    return empleados


def seed_proveedores(db: Session) -> list[Proveedor]:
    """Crea 3 proveedores de ejemplo si la tabla está vacía."""
    if db.query(Proveedor).count() > 0:
        return db.query(Proveedor).all()

    datos_proveedores = [
        {"razon_social": "Distribuidora Belleza Total S.A.C.", "ruc": "20123456781",
         "telefono": "014567890", "correo": "ventas@bellezatotal.com"},
        {"razon_social": "Cosméticos del Perú E.I.R.L.", "ruc": "20123456782",
         "telefono": "014567891", "correo": "contacto@cosmeticosperu.com"},
        {"razon_social": "Importadora Glow S.R.L.", "ruc": "20123456783",
         "telefono": "014567892", "correo": "info@glowimport.com"},
    ]

    proveedores: list[Proveedor] = []
    for datos in datos_proveedores:
        proveedor = Proveedor(
            razon_social=datos["razon_social"],
            documento_ruc=datos["ruc"],
            telefono=datos["telefono"],
            correo=datos["correo"],
            estado=EstadoGenerico.ACTIVO,
        )
        db.add(proveedor)
        proveedores.append(proveedor)

    db.flush()
    db.commit()
    return proveedores


def seed_productos(db: Session, proveedores: list[Proveedor]) -> list[Producto]:
    """Crea categorías y 10 productos de ejemplo, ligados a proveedores."""
    if db.query(Producto).count() > 0:
        return db.query(Producto).all()

    cat_shampoo = CategoriaProducto(nombre="Shampoo y Acondicionador")
    cat_color = CategoriaProducto(nombre="Coloración")
    cat_herramientas = CategoriaProducto(nombre="Herramientas y Accesorios")
    db.add_all([cat_shampoo, cat_color, cat_herramientas])
    db.flush()

    productos_data = [
        {"codigo": "PRD-0001", "nombre": "Shampoo Hidratante 500ml", "categoria": cat_shampoo,
         "marca": "L'Oréal Pro", "compra": Decimal("18.00"), "venta": Decimal("35.00"), "stock": 40},
        {"codigo": "PRD-0002", "nombre": "Acondicionador Reparador 500ml", "categoria": cat_shampoo,
         "marca": "L'Oréal Pro", "compra": Decimal("19.00"), "venta": Decimal("36.00"), "stock": 35},
        {"codigo": "PRD-0003", "nombre": "Shampoo Anticaspa 400ml", "categoria": cat_shampoo,
         "marca": "Nizoral", "compra": Decimal("22.00"), "venta": Decimal("40.00"), "stock": 25},
        {"codigo": "PRD-0004", "nombre": "Tinte Rubio Ceniza 60ml", "categoria": cat_color,
         "marca": "Wella", "compra": Decimal("15.00"), "venta": Decimal("28.00"), "stock": 20},
        {"codigo": "PRD-0005", "nombre": "Tinte Castaño Chocolate 60ml", "categoria": cat_color,
         "marca": "Wella", "compra": Decimal("15.00"), "venta": Decimal("28.00"), "stock": 20},
        {"codigo": "PRD-0006", "nombre": "Oxidante Crema 20 Vol 900ml", "categoria": cat_color,
         "marca": "Wella", "compra": Decimal("12.00"), "venta": Decimal("22.00"), "stock": 30},
        {"codigo": "PRD-0007", "nombre": "Esmalte de Uñas Rojo Clásico", "categoria": cat_herramientas,
         "marca": "OPI", "compra": Decimal("10.00"), "venta": Decimal("18.00"), "stock": 15},
        {"codigo": "PRD-0008", "nombre": "Secadora de Cabello Profesional", "categoria": cat_herramientas,
         "marca": "Babyliss", "compra": Decimal("150.00"), "venta": Decimal("249.00"), "stock": 5},
        {"codigo": "PRD-0009", "nombre": "Plancha de Cabello Cerámica", "categoria": cat_herramientas,
         "marca": "Babyliss", "compra": Decimal("130.00"), "venta": Decimal("219.00"), "stock": 6},
        {"codigo": "PRD-0010", "nombre": "Crema para Peinar 300ml", "categoria": cat_shampoo,
         "marca": "Tresemmé", "compra": Decimal("14.00"), "venta": Decimal("25.00"), "stock": 3},
    ]

    productos: list[Producto] = []
    for idx, datos in enumerate(productos_data):
        producto = Producto(
            categoria_id=datos["categoria"].id,
            proveedor_id=proveedores[idx % len(proveedores)].id if proveedores else None,
            codigo=datos["codigo"],
            nombre=datos["nombre"],
            marca=datos["marca"],
            precio_compra=datos["compra"],
            precio_venta=datos["venta"],
            stock=datos["stock"],
            stock_minimo=10,
            estado=EstadoGenerico.ACTIVO,
        )
        db.add(producto)
        productos.append(producto)

    db.flush()
    db.commit()
    return productos


def seed_promociones(db: Session, servicios: list[Servicio]) -> list[Promocion]:
    """Crea 3 promociones de ejemplo vigentes en distintos rangos de fecha."""
    if db.query(Promocion).count() > 0:
        return db.query(Promocion).all()

    hoy = date.today()
    datos_promociones = [
        {"nombre": "Descuento Coloración de Verano", "porcentaje": Decimal("15.00"),
         "inicio": hoy, "fin": hoy + timedelta(days=30)},
        {"nombre": "Combo Spa Relax", "porcentaje": Decimal("20.00"),
         "inicio": hoy, "fin": hoy + timedelta(days=15)},
        {"nombre": "Promo Manicure + Pedicure", "porcentaje": Decimal("10.00"),
         "inicio": hoy - timedelta(days=5), "fin": hoy + timedelta(days=10)},
    ]

    promociones: list[Promocion] = []
    for datos in datos_promociones:
        promocion = Promocion(
            nombre=datos["nombre"],
            porcentaje_descuento=datos["porcentaje"],
            fecha_inicio=datos["inicio"],
            fecha_fin=datos["fin"],
            activa=True,
        )
        db.add(promocion)
        db.flush()
        if servicios:
            db.add(PromocionServicio(promocion_id=promocion.id, servicio_id=servicios[0].id))
        promociones.append(promocion)

    db.commit()
    return promociones


def seed_configuracion_salon(db: Session) -> ConfiguracionSalon:
    """Crea la fila única de configuración general del salón si no existe."""
    config = db.query(ConfiguracionSalon).first()
    if config:
        return config

    config = ConfiguracionSalon(
        nombre_salon="Salón de Belleza Sinley",
        ruc="10456789012",
        direccion="Av. Principal 123, Lima, Perú",
        telefono="014567890",
        correo="contacto@salonsinley.com",
        moneda="PEN",
        impuesto_porcentaje=Decimal("18.00"),
        horario_general="Lunes a Sábado, 9:00 - 18:00",
        color_principal="#8B5CF6",
        texto_comprobante="Gracias por su preferencia. Vuelva pronto.",
    )
    db.add(config)
    db.commit()
    return config


def run_demo_seed(db: Session) -> None:
    """Ejecuta, en orden, todo el seed de datos de demostración."""
    clientes = seed_clientes(db)
    servicios = seed_categorias_y_servicios(db)
    seed_empleados(db, servicios)
    proveedores = seed_proveedores(db)
    seed_productos(db, proveedores)
    seed_promociones(db, servicios)
    seed_configuracion_salon(db)
    print(f"Seed de demostración completado: {len(clientes)} clientes, {len(servicios)} servicios.")
