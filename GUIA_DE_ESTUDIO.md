# Guía de estudio — Sistema de Gestión de Salón de Belleza

Esta guía te explica el proyecto de punta a punta: arquitectura, cómo viaja una petición desde el clic hasta la base de datos, y los patrones que se repiten en todo el código. Está pensada para que puedas explicar cualquier parte sin depender de memorizar archivos sueltos — si entiendes los patrones, entiendes el 90% del proyecto, porque se repiten en cada módulo (clientes, servicios, empleados, citas, ventas...).

---

## 1. Panorama general

Es una aplicación de **dos proyectos independientes** que se hablan por HTTP/JSON:

```
Navegador (React) ──HTTP/JSON──> API (FastAPI) ──SQL──> PostgreSQL
      :5173                          :8000
```

- **Backend** (`/backend`): Python + FastAPI + SQLAlchemy + PostgreSQL + Alembic. Expone una API REST en `http://localhost:8000/api/v1/...`.
- **Frontend** (`/frontend`): React + TypeScript + Vite + React Router + TanStack Query + Tailwind. Es una SPA (Single Page Application): una sola página HTML que React reescribe dinámicamente.
- No se comparte código ni sesión de servidor entre ambos — la única conexión es la API y un token JWT que el navegador guarda.

**¿Por qué esta separación?** Es el patrón estándar de apps modernas: el backend no sabe nada de botones ni pantallas (solo reglas de negocio y datos), el frontend no sabe nada de SQL (solo consume JSON). Esto permite, por ejemplo, que mañana exista una app móvil que use la misma API sin tocar el backend.

---

## 2. Backend: arquitectura en capas

El backend sigue una **arquitectura en capas** (layered architecture), donde cada capa solo le habla a la de al lado, nunca se salta niveles:

```
Route (FastAPI)  →  Schema (Pydantic)  →  Service  →  Repository  →  Model (SQLAlchemy)  →  PostgreSQL
   "¿qué URL?"         "¿qué forma       "reglas de    "¿cómo se       "¿qué tabla?"
                        tiene el JSON?"    negocio"      consulta?"
```

Carpeta por carpeta (`backend/app/`):

| Carpeta | Qué hace | Ejemplo |
|---|---|---|
| `api/routes/` | Define las URLs (`@router.get(...)`). Solo recibe la petición, valida permisos con `Depends(...)`, y llama al service. **No tiene lógica de negocio.** | `appointment_routes.py` define `POST /appointments` |
| `schemas/` | Clases Pydantic que describen la forma exacta del JSON de entrada/salida. Si el JSON no calza con el schema, FastAPI devuelve `422` automáticamente, antes de que tu código corra. | `CitaCrearRequest` |
| `services/` | El corazón del negocio: validaciones, cálculos, orquestación entre varias tablas. **Aquí está toda la lógica que de verdad importa.** | `AppointmentService.crear()` valida horario, calcula precio, crea la cita |
| `repositories/` | Encapsula las consultas SQL/ORM. Es la única capa que sabe "cómo" se guarda o busca algo en la base. | `CitaRepository.listar()` |
| `models/` | Clases SQLAlchemy que mapean 1 a 1 con las tablas de PostgreSQL. | `Cita`, `Usuario`, `Empleado` |
| `core/` | Configuración transversal: JWT (`security.py`), permisos por rol (`permissions.py`), excepciones (`exceptions.py`), settings desde `.env` (`config.py`). | — |
| `database/` | Conexión a PostgreSQL (`session.py`) y clase base de SQLAlchemy (`base.py`). | — |

> **Dato curioso para la exposición:** hay una carpeta `app/domain/` (entities, value_objects, enums) que está **vacía** — son restos de un intento de aplicar Clean Architecture/DDD que no se terminó de usar. Si te preguntan, es honesto decir "existe pero no se usa; la lógica real vive en `services/`".

### 2.1 El patrón de respuesta uniforme

Todas las respuestas de la API tienen la misma forma, gracias a wrappers genéricos en `schemas/common_schema.py`:

```python
RespuestaExito[T]      # { "message": "...", "data": T }
RespuestaPaginada[T]   # { "items": [...], "total": N, "pagina": 1, "total_paginas": N }
RespuestaMensaje       # { "message": "..." }
```

Por eso en el frontend siempre ves `response.data.data` (el primer `.data` es de axios, el segundo es el de `RespuestaExito`).

### 2.2 Manejo de errores centralizado

En vez de `try/except` repetido en cada endpoint, el proyecto define excepciones propias en `core/exceptions.py` (`NotFoundException`, `ConflictException`, `ValidationException`, `UnauthorizedException`, `ForbiddenException`), cada una con su código HTTP. Un handler global (`core/error_handlers.py`, registrado en `main.py`) las intercepta y las convierte en JSON consistente. Así, un service simplemente hace:

```python
if not cliente: raise NotFoundException("El cliente no existe")
```

y el resto es automático (404 + mensaje JSON).

### 2.3 Autenticación y roles (JWT)

1. `POST /auth/login` recibe correo+contraseña → `AuthService` verifica el hash (bcrypt, `core/security.py`) → si es válido, genera dos JWT: un **access token** (dura 60 min) y un **refresh token** (dura 7 días).
2. El frontend guarda ambos en `localStorage` y manda el access token en cada petición: header `Authorization: Bearer <token>`.
3. `api/dependencies.py::get_current_user` es una **dependencia de FastAPI** que se inyecta en casi todas las rutas (`Depends(get_current_user)`): decodifica el JWT, busca al usuario en la BD, y lo devuelve. Si el token es inválido/expiró/el usuario está inactivo → `401`.
4. Los **roles** (ADMINISTRADOR, RECEPCIONISTA, ESTILISTA, CLIENTE) se validan con `core/permissions.py::require_roles(...)`, otra dependencia que se agrega en el decorador de la ruta:
   ```python
   @router.delete("/{id}", dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
   ```
   Si el usuario no tiene ese rol → `403`.
5. Cuando el access token expira, el interceptor de axios en el frontend (`frontend/src/api/http.ts`) detecta el `401`, llama automáticamente a `POST /auth/refresh` con el refresh token, y reintenta la petición original — el usuario nunca lo nota.

---

## 3. Frontend: cómo está armado

```
main.tsx           → punto de entrada, monta <App/> dentro de <AuthProvider>
App.tsx            → define TODAS las rutas (React Router) y qué rol puede ver cada una
auth/AuthContext.tsx → guarda el usuario logueado en memoria (Context API de React)
api/http.ts         → instancia única de axios: agrega el JWT a cada petición, maneja el refresh automático
layout/AppLayout.tsx → el menú lateral + header (para admin/recepción/estilista)
layout/ClientLayout.tsx → layout distinto para el portal del cliente
pages/*.tsx          → una página por pantalla (Clientes, Agenda, POS, etc.)
components/*.tsx     → piezas reutilizables (Modal, Pagination, StatusBadge)
types.ts             → tipos TypeScript que describen la forma de los datos que manda la API
```

### 3.1 Control de acceso por rol en el frontend

Esto pasa en **dos niveles**, y hay que entender que son independientes:

1. **Backend** (`require_roles`): la verdad absoluta. Si el rol no tiene permiso, la API rechaza la petición pase lo que pase en el frontend.
2. **Frontend** (`<RoleRoute roles={[...]}>` en `App.tsx` + el array `items` en `AppLayout.tsx`): solo controla qué **ve** el usuario (oculta botones/rutas para que la experiencia sea coherente). Si el frontend permite algo que el backend no, la API simplemente devuelve `403` — no es un hueco de seguridad, es solo una mala experiencia de usuario. **Este fue justamente uno de los bugs que corregimos**: el frontend bloqueaba a RECEPCIONISTA de ver Inventario/Reportes aunque el backend sí lo permitía.

### 3.2 TanStack Query (`useQuery` / `useMutation`)

Casi todas las páginas siguen este patrón:

```tsx
const {data} = useQuery({
  queryKey: ['clientes', page],          // identifica el caché
  queryFn: async () => (await http.get('/clients', {params:{pagina:page}})).data
});

const save = useMutation({
  mutationFn: () => http.post('/clients', form),
  onSuccess: () => qc.invalidateQueries({queryKey:['clientes']})  // refresca la lista
});
```

`useQuery` trae datos y los cachea; `useMutation` hace cambios (crear/editar/borrar) y luego invalida el caché para que la lista se refresque sola. Nunca vas a ver un `useState` + `useEffect` manual para pedir datos — eso es justamente lo que TanStack Query reemplaza.

---

## 4. Traza completa de una petición: "crear una cita"

La forma más rápida de entender TODO el proyecto es seguir una sola acción de punta a punta. Usamos "el cliente reserva una cita" porque toca casi todas las capas:

1. **Frontend — `ClientAppointmentsPage.tsx`**: el usuario llena el formulario (servicios, profesional, fecha, hora) y hace submit. Se dispara:
   ```tsx
   http.post('/client-portal/appointments', f)
   ```
2. **`api/http.ts`**: el interceptor le agrega el header `Authorization: Bearer <token>` antes de que salga la petición.
3. **Backend — `client_portal_routes.py::crear_cita`**: FastAPI valida el JSON contra `PortalCitaCrearRequest` (Pydantic). Si falta un campo o el tipo no calza → `422` automático, sin que tu código corra.
4. La ruta arma un `CitaCrearRequest` (agregando el `cliente_id` del usuario logueado) y llama a `AppointmentService(db).crear(req, user)`.
5. **`AppointmentService.crear()`** (la lógica de negocio real):
   - Verifica que el cliente y el empleado existan y estén activos.
   - Verifica que el empleado esté habilitado para **todos** los servicios pedidos.
   - Calcula duración total y precio total sumando cada servicio.
   - Calcula la hora de fin.
   - Llama a `verificar_disponibilidad()`: chequea horario laboral, descanso, vacaciones, bloqueos, y que no choque con otra cita.
   - Si todo pasa, crea el objeto `Cita` (modelo SQLAlchemy) y lo guarda vía `CitaRepository.guardar()`.
6. **`CitaRepository`** hace el `INSERT` real contra PostgreSQL (a través del `Session` de SQLAlchemy).
7. La respuesta viaja de vuelta: modelo → `CitaResponse` (Pydantic) → `RespuestaExito` → JSON → axios → React Query invalida el caché → la pantalla se actualiza sola mostrando la nueva cita.

Si puedes explicar estos 7 pasos con tus propias palabras, puedes explicar cualquier otro flujo del sistema (crear un cliente, una venta, un producto...) porque **todos siguen exactamente esta misma forma**.

---

## 5. Los módulos de negocio (mapa rápido)

| Módulo | Backend (routes + service) | Frontend (pages) | Qué resuelve |
|---|---|---|---|
| Autenticación | `auth_routes.py` / `AuthService` | `LoginPage`, `AuthContext` | Login, JWT, cambio de contraseña |
| Clientes | `client_routes.py` | `ClientsPage` | CRUD de clientes + acceso al portal |
| Servicios/Empleados | `service_routes.py`, `employee_routes.py` | `CatalogPage` (genérico para ambos) | Catálogo del salón |
| Agenda/Citas | `appointment_routes.py` / `AppointmentService` | `AgendaPage`, `ClientAppointmentsPage` | Reservas, disponibilidad, estados |
| Inventario/Compras | `inventory_routes.py` | `ProductsPage`, `PurchasesPage` | Productos, proveedores, stock, compras |
| Ventas/POS | `sale_routes.py` / `SaleService` | `POSPage`, `SalesPage` | Cobros, comisiones automáticas, stock |
| Comisiones | `finance_routes.py` | `CommissionsPage` | Cuánto gana cada estilista por venta |
| Pedidos online | `finance_routes.py` (`/online-orders`) | `OnlineOrdersPage`, `ClientShopPage` | Tienda del cliente, pago en salón |
| Reportes | `report_routes.py` | `ReportsPage`, `DashboardPage` | Dashboard, exportaciones Excel/PDF |
| Auditoría | `finance_routes.py` (`/finance/audit`) | `AuditPage` | Quién hizo qué y cuándo (trazabilidad) |
| Portal del cliente | `client_portal_routes.py` | `Client*Page` (todas) | Vista separada, sin acceso admin |

**Nota:** el módulo de Caja se retiró (backend y frontend) por decisión de producto durante las correcciones — si buscas `CajaSesion`/`CajaMovimiento` en los modelos, siguen ahí (la tabla existe), pero ya no tiene rutas ni pantalla.

---

## 6. Base de datos y migraciones (Alembic)

- Las tablas **no se crean escribiendo SQL a mano**: se definen como clases Python en `models/*.py` (SQLAlchemy), y Alembic genera y aplica los cambios.
- `alembic upgrade head` lee las migraciones en `backend/alembic/versions/` y las aplica en orden — cada una es un paso incremental ("agregar tabla X", "agregar columna Y").
- Si cambias un modelo (agregas un campo), necesitas generar una migración nueva; no basta con editar el archivo Python.
- `backend/app/seed/professional_seed.py` no toca Alembic — asume que las tablas ya existen y solo **inserta datos de prueba** directamente (por eso vimos que no pasa por las validaciones normales de negocio, a diferencia de cuando un usuario real crea algo desde la interfaz).

---

## 7. Preguntas típicas que te pueden hacer (y cómo responderlas)

- **"¿Por qué separaron routes de services?"** → Para que la lógica de negocio no dependa de HTTP. Si mañana agregan una tarea programada (cron) que también necesita "crear una cita", puede llamar directo a `AppointmentService`, sin pasar por FastAPI.
- **"¿Qué pasa si dos personas editan lo mismo a la vez?"** → SQLAlchemy usa transacciones (`db.commit()` al final de cada operación); no hay locking optimista explícito en la mayoría de los services, así que en un conflicto real gana el último `commit()`. Es una limitación conocida, no un diseño perfecto.
- **"¿Cómo se protege una contraseña?"** → Nunca se guarda en texto plano: `core/security.py` usa `bcrypt` (vía `passlib`) para generar un hash de un solo sentido; el login compara hashes, no las contraseñas mismas.
- **"¿Qué pasa si el token expira a la mitad de una sesión?"** → El interceptor de axios en `http.ts` lo detecta (`401`), pide un token nuevo con el refresh token, y reintenta — transparente para el usuario, hasta que el refresh también expira (7 días), ahí sí se cierra la sesión.
- **"¿Por qué algunos endpoints no tienen `/prefix` propio?"** (p. ej. `sale_routes.py` mezcla `/sales` y `/cash`) → Es una decisión de organización del código, no de la API en sí: varios recursos relacionados (ventas y su caja) comparten un mismo archivo de rutas aunque tengan distinto prefijo de URL.

---

## 8. Cómo estudiarlo tú mismo (sin depender de esta guía)

1. Elige **una sola acción de negocio** (ej. "editar un empleado") y ábrela en las 5 capas en orden: route → schema → service → repository → model. Repite con 2-3 acciones más — verás que el molde se repite.
2. En el frontend, abre una página completa (`ClientsPage.tsx` es un buen ejemplo mediano) y ubica: el `useQuery` que trae la lista, el `useMutation` que guarda, y el JSX que arma la tabla y el modal.
3. Corre el backend con `--reload` y abre `http://localhost:8000/docs` (Swagger): ahí puedes probar cualquier endpoint a mano y ver exactamente qué JSON espera y qué devuelve, sin tocar el frontend.
4. Para explicar el sistema de roles, dibuja una tabla: filas = las 4 rutas más importantes (Inventario, Reportes, Comisiones, Auditoría), columnas = los 4 roles, y marca quién puede hacer qué — así queda clarísimo en una sola imagen.
