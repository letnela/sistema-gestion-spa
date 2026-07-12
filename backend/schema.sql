-- =========================================================================
-- SCRIPT SQL DE CREACION DE ESQUEMA COMPLETO
-- Sistema de Gestion de Salon de Belleza
-- Base de datos: peluqueria
-- Este script es equivalente a la migracion Alembic 0001_initial_schema.
-- Uso recomendado: dejar que Alembic gestione el esquema (alembic upgrade head).
-- Este script se entrega como referencia / opcion de creacion manual.
-- =========================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================
-- roles
-- =====================
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_roles_nombre ON roles (nombre);

-- =====================
-- usuarios
-- =====================
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre_completo VARCHAR(150) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol_id UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    estado VARCHAR(20) NOT NULL,
    telefono VARCHAR(30),
    avatar_url VARCHAR(500),
    ultimo_login TIMESTAMPTZ,
    debe_cambiar_password BOOLEAN NOT NULL DEFAULT FALSE,
    intentos_fallidos INTEGER NOT NULL DEFAULT 0,
    bloqueado_hasta TIMESTAMPTZ,
    reset_password_token VARCHAR(255),
    reset_password_expira TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_usuarios_correo ON usuarios (correo);

-- =====================
-- intentos_login
-- =====================
CREATE TABLE intentos_login (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    correo_intentado VARCHAR(150) NOT NULL,
    exitoso BOOLEAN NOT NULL,
    ip_origen VARCHAR(50),
    navegador VARCHAR(255),
    fecha TIMESTAMPTZ NOT NULL
);

-- =====================
-- clientes
-- =====================
CREATE TABLE clientes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    documento VARCHAR(30) UNIQUE,
    telefono VARCHAR(30),
    correo VARCHAR(150),
    direccion VARCHAR(255),
    fecha_nacimiento DATE,
    observaciones TEXT,
    preferencias TEXT,
    alergias TEXT,
    estado VARCHAR(20) NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES usuarios(id) ON DELETE SET NULL
);

-- =====================
-- empleados
-- =====================
CREATE TABLE empleados (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID UNIQUE REFERENCES usuarios(id) ON DELETE SET NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    documento VARCHAR(30) UNIQUE,
    telefono VARCHAR(30),
    correo VARCHAR(150),
    cargo VARCHAR(100) NOT NULL,
    especialidad VARCHAR(150),
    salario NUMERIC(10,2),
    porcentaje_comision_default NUMERIC(5,2) NOT NULL DEFAULT 10.00,
    fecha_ingreso DATE NOT NULL,
    estado VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================
-- categorias_servicio / servicios
-- =====================
CREATE TABLE categorias_servicio (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    estado VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE servicios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    categoria_id UUID NOT NULL REFERENCES categorias_servicio(id) ON DELETE RESTRICT,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    precio NUMERIC(10,2) NOT NULL,
    duracion_minutos INTEGER NOT NULL,
    imagen_url VARCHAR(500),
    porcentaje_comision NUMERIC(5,2) NOT NULL DEFAULT 10.00,
    estado VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================
-- empleado_servicio / horarios / vacaciones / bloqueos
-- =====================
CREATE TABLE empleado_servicio (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empleado_id UUID NOT NULL REFERENCES empleados(id) ON DELETE CASCADE,
    servicio_id UUID NOT NULL REFERENCES servicios(id) ON DELETE CASCADE,
    UNIQUE (empleado_id, servicio_id)
);

CREATE TABLE horarios_empleado (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empleado_id UUID NOT NULL REFERENCES empleados(id) ON DELETE CASCADE,
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),
    hora_entrada TIME NOT NULL,
    hora_salida TIME NOT NULL,
    hora_inicio_descanso TIME,
    hora_fin_descanso TIME,
    es_dia_libre BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (empleado_id, dia_semana)
);

CREATE TABLE vacaciones_empleado (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empleado_id UUID NOT NULL REFERENCES empleados(id) ON DELETE CASCADE,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL CHECK (fecha_fin >= fecha_inicio),
    motivo VARCHAR(255),
    aprobado BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE bloqueos_horario (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empleado_id UUID NOT NULL REFERENCES empleados(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    motivo TEXT
);

-- =====================
-- categorias_producto / proveedores / productos / proveedor_producto
-- =====================
CREATE TABLE categorias_producto (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    estado VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE proveedores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    razon_social VARCHAR(150) NOT NULL,
    documento_ruc VARCHAR(30) NOT NULL UNIQUE,
    telefono VARCHAR(30),
    correo VARCHAR(150),
    direccion VARCHAR(255),
    contacto_nombre VARCHAR(150),
    estado VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE productos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    categoria_id UUID NOT NULL REFERENCES categorias_producto(id) ON DELETE RESTRICT,
    proveedor_id UUID REFERENCES proveedores(id) ON DELETE SET NULL,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    marca VARCHAR(100),
    descripcion TEXT,
    precio_compra NUMERIC(10,2) NOT NULL,
    precio_venta NUMERIC(10,2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    stock_minimo INTEGER NOT NULL DEFAULT 5,
    imagen_url VARCHAR(500),
    estado VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_productos_codigo ON productos (codigo);

CREATE TABLE proveedor_producto (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    proveedor_id UUID NOT NULL REFERENCES proveedores(id) ON DELETE CASCADE,
    producto_id UUID NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    UNIQUE (proveedor_id, producto_id)
);

-- =====================
-- citas / cita_servicios
-- =====================
CREATE TABLE citas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cliente_id UUID NOT NULL REFERENCES clientes(id) ON DELETE RESTRICT,
    empleado_id UUID NOT NULL REFERENCES empleados(id) ON DELETE RESTRICT,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    duracion_total_minutos INTEGER NOT NULL DEFAULT 0,
    precio_total NUMERIC(10,2) NOT NULL DEFAULT 0,
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('PENDIENTE','CONFIRMADA','EN_PROCESO','FINALIZADA','CANCELADA','NO_ASISTIO')),
    notas TEXT,
    motivo_cancelacion VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES usuarios(id) ON DELETE SET NULL
);
CREATE INDEX ix_citas_fecha ON citas (fecha);
CREATE INDEX ix_citas_empleado_fecha ON citas (empleado_id, fecha);

CREATE TABLE cita_servicios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cita_id UUID NOT NULL REFERENCES citas(id) ON DELETE CASCADE,
    servicio_id UUID NOT NULL REFERENCES servicios(id) ON DELETE RESTRICT,
    precio_aplicado NUMERIC(10,2) NOT NULL,
    duracion_aplicada_minutos INTEGER NOT NULL
);

-- =====================
-- inventario_movimientos
-- =====================
CREATE TABLE inventario_movimientos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    producto_id UUID NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('ENTRADA','SALIDA','AJUSTE')),
    cantidad INTEGER NOT NULL,
    stock_resultante INTEGER NOT NULL CHECK (stock_resultante >= 0),
    motivo TEXT NOT NULL,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    fecha TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================
-- ventas / venta_detalles
-- =====================
CREATE TABLE ventas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    numero_comprobante VARCHAR(50) NOT NULL UNIQUE,
    cliente_id UUID REFERENCES clientes(id) ON DELETE SET NULL,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    subtotal NUMERIC(10,2) NOT NULL DEFAULT 0,
    descuento NUMERIC(10,2) NOT NULL DEFAULT 0,
    impuesto NUMERIC(10,2) NOT NULL DEFAULT 0,
    total NUMERIC(10,2) NOT NULL DEFAULT 0,
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('COMPLETADA','ANULADA')),
    motivo_anulacion VARCHAR(255),
    fecha TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES usuarios(id) ON DELETE SET NULL
);
CREATE INDEX ix_ventas_numero_comprobante ON ventas (numero_comprobante);
CREATE INDEX ix_ventas_fecha ON ventas (fecha);

CREATE TABLE venta_detalles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    venta_id UUID NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    producto_id UUID REFERENCES productos(id) ON DELETE RESTRICT,
    servicio_id UUID REFERENCES servicios(id) ON DELETE RESTRICT,
    empleado_id UUID REFERENCES empleados(id) ON DELETE SET NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    precio_unitario NUMERIC(10,2) NOT NULL,
    descuento NUMERIC(10,2) NOT NULL DEFAULT 0,
    subtotal NUMERIC(10,2) NOT NULL,
    CHECK (
        (producto_id IS NOT NULL AND servicio_id IS NULL) OR
        (producto_id IS NULL AND servicio_id IS NOT NULL)
    )
);

-- =====================
-- pagos
-- =====================
CREATE TABLE pagos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    venta_id UUID NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    monto NUMERIC(10,2) NOT NULL CHECK (monto > 0),
    metodo VARCHAR(30) NOT NULL CHECK (metodo IN ('EFECTIVO','TARJETA','TRANSFERENCIA','YAPE','PLIN')),
    referencia VARCHAR(150),
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('PENDIENTE','PARCIAL','COMPLETO','ANULADO')),
    fecha TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================
-- promociones / promocion_servicios / promocion_productos
-- =====================
CREATE TABLE promociones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    porcentaje_descuento NUMERIC(5,2) NOT NULL CHECK (porcentaje_descuento > 0 AND porcentaje_descuento <= 100),
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL CHECK (fecha_fin >= fecha_inicio),
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE promocion_servicios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    promocion_id UUID NOT NULL REFERENCES promociones(id) ON DELETE CASCADE,
    servicio_id UUID NOT NULL REFERENCES servicios(id) ON DELETE CASCADE,
    UNIQUE (promocion_id, servicio_id)
);

CREATE TABLE promocion_productos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    promocion_id UUID NOT NULL REFERENCES promociones(id) ON DELETE CASCADE,
    producto_id UUID NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    UNIQUE (promocion_id, producto_id)
);

-- =====================
-- comisiones
-- =====================
CREATE TABLE comisiones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empleado_id UUID NOT NULL REFERENCES empleados(id) ON DELETE CASCADE,
    venta_id UUID REFERENCES ventas(id) ON DELETE SET NULL,
    tipo VARCHAR(30) NOT NULL CHECK (tipo IN ('SERVICIO','VENTA_PRODUCTO')),
    monto_base NUMERIC(10,2) NOT NULL,
    porcentaje_aplicado NUMERIC(5,2) NOT NULL,
    monto_comision NUMERIC(10,2) NOT NULL,
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('PENDIENTE','PAGADA')),
    periodo DATE NOT NULL,
    fecha_pago TIMESTAMPTZ,
    fecha TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================
-- auditoria / notificaciones
-- =====================
CREATE TABLE auditoria (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    accion VARCHAR(30) NOT NULL,
    modulo VARCHAR(100) NOT NULL,
    entidad VARCHAR(100) NOT NULL,
    entidad_id VARCHAR(100),
    valor_anterior JSONB,
    valor_nuevo JSONB,
    ip_origen VARCHAR(50),
    navegador VARCHAR(255),
    fecha TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_auditoria_fecha ON auditoria (fecha);
CREATE INDEX ix_auditoria_entidad ON auditoria (entidad, entidad_id);

CREATE TABLE notificaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo VARCHAR(150) NOT NULL,
    mensaje TEXT NOT NULL,
    leida BOOLEAN NOT NULL DEFAULT FALSE,
    tipo VARCHAR(50) NOT NULL,
    fecha TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================
-- configuracion_salon
-- =====================
CREATE TABLE configuracion_salon (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre_salon VARCHAR(150) NOT NULL,
    logo_url VARCHAR(500),
    ruc VARCHAR(30),
    direccion VARCHAR(255),
    telefono VARCHAR(30),
    correo VARCHAR(150),
    moneda VARCHAR(10) NOT NULL DEFAULT 'PEN',
    impuesto_porcentaje NUMERIC(5,2) NOT NULL DEFAULT 18.00,
    horario_general VARCHAR(255),
    color_principal VARCHAR(20) NOT NULL DEFAULT '#8B5CF6',
    texto_comprobante TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
