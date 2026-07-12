# Sistema de Gestión de Salón de Belleza — Backend

Backend construido con **FastAPI + SQLAlchemy 2 + PostgreSQL + Alembic**, en arquitectura
por capas (core, database, models, schemas, repositories, services, use_cases, api).

## FASE 1 y FASE 2 — Estado actual

**Fase 1** entregó: arquitectura del proyecto, configuración, conexión a base de datos,
todos los modelos ORM (28 tablas) y la migración inicial completa (Alembic + script SQL puro).

**Fase 2** entrega: **autenticación completa (login, logout, JWT access/refresh, cambio y
recuperación de contraseña, bloqueo temporal por intentos fallidos, auditoría de login) y
gestión administrativa de usuarios (crear, editar, listar con filtros/búsqueda/paginación,
activar/inactivar, cambiar rol, restablecer contraseña)**, con permisos por rol aplicados
mediante `require_roles()`.

Los routers de clientes, empleados, servicios, citas, etc. se agregan a partir de la Fase 3.

## 1. Requisitos previos

- Python 3.11+
- PostgreSQL 14+ corriendo en `localhost:5432`
- pip / virtualenv

## 2. Crear la base de datos y el usuario en PostgreSQL

Conéctate a PostgreSQL como superusuario (`psql -U postgres`) y ejecuta:

```sql
CREATE USER peluqueria_user WITH PASSWORD 'Sinley123.';
CREATE DATABASE peluqueria OWNER peluqueria_user;
GRANT ALL PRIVILEGES ON DATABASE peluqueria TO peluqueria_user;
```

## 3. Configurar el entorno virtual e instalar dependencias

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Configurar variables de entorno

```bash
cp .env.example .env
```

El archivo `.env.example` ya trae los valores por defecto solicitados
(`peluqueria` / `peluqueria_user` / `Sinley123.` / `localhost` / `5432`).
Ajusta `SECRET_KEY` antes de pasar a producción.

## 5. Ejecutar las migraciones (crea las 28 tablas)

```bash
alembic upgrade head
```

Esto ejecuta la migración `0001_initial_schema`, que crea todas las tablas,
llaves foráneas, índices, restricciones únicas y check constraints.

> Alternativa manual: también se entrega `schema.sql`, un script SQL puro
> equivalente, por si prefieres crear el esquema directamente con `psql`:
> `psql -U peluqueria_user -d peluqueria -f schema.sql`
> (usa una u otra opción, no ambas, para evitar conflictos de tablas duplicadas).

## 6. Cargar los datos iniciales (seed)

```bash
python -m app.seed.run_seed
```

Esto crea:
- Los 3 roles del sistema (ADMINISTRADOR, RECEPCIONISTA, ESTILISTA)
- Los 3 usuarios iniciales (ver credenciales abajo)
- 5 clientes, 3 empleados (con horarios y servicios asignados), 8 servicios,
  10 productos, 3 proveedores y 3 promociones de ejemplo
- La configuración general del salón

## 7. Ejecutar el servidor

```bash
python run.py
```

o directamente con uvicorn:

```bash
uvicorn app.main:app --reload
```

La API queda disponible en `http://localhost:8000`, con Swagger en
`http://localhost:8000/docs` y Redoc en `http://localhost:8000/redoc`.

## 8. Ejecutar las pruebas básicas

```bash
pytest
```

## Credenciales iniciales

| Rol            | Correo                | Contraseña       |
|----------------|------------------------|-------------------|
| Administrador  | admin@salon.com        | Admin123*         |
| Recepcionista  | recepcion@salon.com    | Recepcion123*     |
| Estilista      | estilista@salon.com    | Estilista123*     |

## Estructura del proyecto (Fase 1)

```
backend/
├── app/
│   ├── main.py                  # Entrypoint FastAPI (CORS, error handlers, health check)
│   ├── core/
│   │   ├── config.py            # Configuración vía variables de entorno
│   │   ├── security.py          # Hash de contraseñas y JWT
│   │   ├── permissions.py       # Dependencia require_roles() para RBAC
│   │   ├── exceptions.py        # Excepciones de dominio
│   │   ├── error_handlers.py    # Manejadores globales -> respuestas JSON consistentes
│   │   └── constants.py         # Roles, estados, enums de negocio
│   ├── database/
│   │   ├── base.py              # Base declarativa + mixins (Timestamp, AuditUser)
│   │   ├── session.py           # Engine, SessionLocal, get_db()
│   │   └── transaction.py       # Context manager para transacciones atómicas
│   ├── models/                  # 15 archivos, 28 tablas mapeadas con SQLAlchemy 2
│   └── seed/
│       ├── roles_seed.py
│       ├── admin_seed.py
│       ├── demo_seed.py
│       └── run_seed.py
├── alembic/
│   ├── env.py
│   └── versions/0001_initial_schema.py
├── tests/test_main.py
├── schema.sql                   # Script SQL puro equivalente
├── requirements.txt
├── .env.example
├── alembic.ini
├── run.py
└── README.md
```

## Endpoints disponibles (Fase 2)

**Autenticación** (`/api/v1/auth`):
- `POST /login` — Iniciar sesión (retorna access + refresh token)
- `POST /refresh` — Renovar token de acceso
- `POST /logout` — Cerrar sesión (requiere token)
- `GET /me` — Perfil del usuario autenticado (requiere token)
- `PUT /change-password` — Cambiar contraseña propia (requiere token)
- `POST /forgot-password` — Solicitar recuperación de contraseña
- `POST /reset-password` — Restablecer contraseña con token de recuperación

**Usuarios** (`/api/v1/users`, solo rol ADMINISTRADOR):
- `GET /` — Listar usuarios (filtros: rol, estado, búsqueda; paginado)
- `POST /` — Crear usuario
- `GET /{id}` — Obtener usuario
- `PUT /{id}` — Editar usuario
- `PATCH /{id}/status` — Activar/Inactivar usuario
- `PATCH /{id}/role` — Cambiar rol
- `PATCH /{id}/reset-password` — Restablecer contraseña (genera una temporal)

## Checklist de validación — Fase 1 y Fase 2

- [x] `pip install -r requirements.txt` instala sin errores
- [x] `alembic upgrade head` crea las 28 tablas sin errores
- [x] `python -m app.seed.run_seed` puebla roles, usuarios y datos demo
- [x] `python run.py` levanta el servidor en el puerto 8000
- [x] `GET /` responde 200 con estado "activo"
- [x] `GET /health` responde `{"status": "ok"}`
- [x] `GET /docs` muestra Swagger, incluyendo los endpoints de auth y usuarios
- [x] `POST /api/v1/auth/login` con `admin@salon.com` / `Admin123*` retorna tokens
- [x] `GET /api/v1/auth/me` con el token retorna el perfil correcto
- [x] `GET /api/v1/users` con un token de ESTILISTA retorna 403 (permisos por rol funcionando)
- [x] 5 intentos fallidos de login bloquean la cuenta temporalmente (`MAX_LOGIN_ATTEMPTS`)
- [x] `pytest` pasa las pruebas de `test_main.py` y `test_auth.py` (requieren BD activa y seed cargado)
- [x] Todos los modelos usan type hints, docstrings en español y UUID como PK
- [x] Las rutas no contienen lógica de negocio (delegada 100% a `services/`)

## Próximas fases

- **Fase 2:** Autenticación (login/logout/JWT/refresh), gestión de usuarios y permisos por rol.
- **Fase 3:** Clientes, empleados, servicios, horarios y citas (con validación de disponibilidad).
- **Fase 4:** Productos, proveedores e inventario (kardex, alertas de stock).
- **Fase 5:** Ventas, pagos, promociones y comisiones.
- **Fase 6:** Dashboard, reportes, auditoría y configuración del salón.
- **Fase 7-9:** Frontend React completo, integración y pruebas finales.

## Fase 3 - Gestión de clientes

Endpoints agregados bajo `/api/v1/clients`:

- `GET /api/v1/clients`: listado con búsqueda, estado, orden y paginación.
- `POST /api/v1/clients`: creación de clientes.
- `GET /api/v1/clients/{cliente_id}`: detalle de cliente.
- `PUT /api/v1/clients/{cliente_id}`: actualización.
- `PATCH /api/v1/clients/{cliente_id}/status`: activación o inactivación.
- `DELETE /api/v1/clients/{cliente_id}`: eliminación lógica (solo administrador).

Administrador y recepcionista pueden crear y editar. El estilista tiene acceso de consulta. La eliminación queda restringida al administrador.

## Fase 4 - Catálogo de servicios

Esta fase incorpora la administración completa de categorías y servicios del salón.

### Endpoints de categorías

- `GET /api/v1/services/categories`
- `POST /api/v1/services/categories`
- `GET /api/v1/services/categories/{categoria_id}`
- `PUT /api/v1/services/categories/{categoria_id}`
- `PATCH /api/v1/services/categories/{categoria_id}/status`
- `DELETE /api/v1/services/categories/{categoria_id}`

### Endpoints de servicios

- `GET /api/v1/services`
- `POST /api/v1/services`
- `GET /api/v1/services/{servicio_id}`
- `PUT /api/v1/services/{servicio_id}`
- `PATCH /api/v1/services/{servicio_id}/status`
- `DELETE /api/v1/services/{servicio_id}`

Los listados permiten búsqueda, paginación, ordenamiento, filtro por estado y categoría;
el listado de servicios también permite filtrar por rango de precios. Las operaciones de
escritura son exclusivas del rol `ADMINISTRADOR`; recepcionistas y estilistas pueden consultar.

## Fase 5 - Gestión de empleados

Esta versión incorpora el módulo completo de empleados:

- CRUD y búsqueda paginada de empleados.
- Filtros por estado y cargo.
- Vinculación opcional con una cuenta de usuario.
- Especialidad, salario y porcentaje de comisión predeterminado.
- Asignación de múltiples servicios activos por empleado.
- Configuración del horario semanal y descansos.
- Registro de vacaciones con validación de cruces.
- Bloqueos puntuales de agenda con validación de solapamientos.
- Activación, inactivación y auditoría.
- Permisos por rol y pruebas de validación.

### Endpoints principales

- `GET /api/v1/employees`
- `POST /api/v1/employees`
- `GET /api/v1/employees/{id}`
- `PUT /api/v1/employees/{id}`
- `PATCH /api/v1/employees/{id}/status`
- `DELETE /api/v1/employees/{id}`
- `PUT /api/v1/employees/{id}/schedule/{dia_semana}`
- `POST /api/v1/employees/{id}/vacations`
- `POST /api/v1/employees/{id}/blocks`

## Fase 6 - Agenda y citas

Endpoints disponibles bajo `/api/v1/appointments`:

- `GET /appointments`: agenda paginada con filtros por fechas, empleado, cliente y estado.
- `GET /appointments/{id}`: detalle completo de una cita.
- `POST /appointments`: crea una cita con uno o varios servicios.
- `PUT /appointments/{id}`: reprograma o edita una cita pendiente/confirmada.
- `PATCH /appointments/{id}/status`: confirma, inicia, finaliza, cancela o marca ausencia.
- `DELETE /appointments/{id}`: eliminación administrativa.
- `GET /appointments/availability`: verifica disponibilidad puntual.

La duración y el precio se calculan automáticamente con los servicios seleccionados. Se validan horario laboral, descanso, vacaciones, bloqueos, servicios habilitados y cruces con otras citas.

## Fase 7 - Ventas, caja y pagos

Esta fase añade el punto de venta transaccional:

- Ventas de productos y servicios en una misma operación.
- Uno o varios métodos de pago por venta.
- Validación de referencias para tarjeta, transferencia, Yape y Plin.
- Cálculo de subtotal, descuentos, impuesto y total.
- Validación de que los pagos cubran exactamente el total.
- Descuento automático de stock y registro en kardex.
- Generación automática de comisiones por servicios.
- Anulación de ventas con devolución de stock y anulación de pagos.
- Apertura, movimientos y cierre de caja con diferencia calculada.
- Auditoría y permisos por rol.

Antes de iniciar el backend, ejecute la nueva migración:

```powershell
alembic upgrade head
```

Rutas principales:

- `POST /api/v1/sales`
- `GET /api/v1/sales`
- `GET /api/v1/sales/{venta_id}`
- `PATCH /api/v1/sales/{venta_id}/cancel`
- `POST /api/v1/cash/open`
- `GET /api/v1/cash/current`
- `POST /api/v1/cash/movements`
- `POST /api/v1/cash/close`

## Fase 8 - Inventario y Proveedores

Incluye categorías de producto, productos con SKU/código de barras, proveedores, compras con múltiples detalles, kardex, ajustes manuales, alertas de stock mínimo y resumen valorizado del inventario.

Antes de ejecutar esta versión:

```bash
alembic upgrade head
```

Rutas principales: `/api/v1/products`, `/api/v1/suppliers`, `/api/v1/purchases`, `/api/v1/inventory/kardex/{producto_id}`, `/api/v1/inventory/alerts` y `/api/v1/inventory/summary`.

## Fase 9 - Dashboard y Reportes

Se agregaron indicadores ejecutivos y reportes analíticos bajo `/api/v1/reports`:

- `GET /reports/dashboard`: KPIs, ventas diarias, citas por estado y rankings.
- `GET /reports/sales`: ventas, descuentos, impuestos, ticket promedio y métodos de pago.
- `GET /reports/appointments`: productividad de citas, servicios y empleados.
- `GET /reports/inventory`: valoración y alertas de inventario.
- `GET /reports/sales/export.xlsx`: exportación de ventas a Excel.
- `GET /reports/executive/export.pdf`: reporte ejecutivo en PDF.

El rango predeterminado es de los últimos 30 días y el máximo permitido es de 366 días.
