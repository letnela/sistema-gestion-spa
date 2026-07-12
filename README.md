# Sistema de Gestión para Salón de Belleza — Fase 21 (Premium Responsive)

Proyecto completo con backend FastAPI/PostgreSQL y frontend React/Vite/TypeScript.
Este documento cubre la evolución completa del sistema, desde el CRUD administrativo
inicial (Fase 12) hasta la experiencia premium responsive actual (Fase 21). El historial
detallado de cada fase se conserva más abajo como referencia.

## Estructura

- `backend/`: API, autenticación JWT, clientes, servicios, empleados, citas, ventas, caja, inventario y reportes.
- `frontend/`: interfaz responsive conectada a la API.

## 1. Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python -m app.seed.run_seed
uvicorn app.main:app --reload
```

API: `http://localhost:8000`
Swagger: `http://localhost:8000/docs`

## 2. Frontend

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

Frontend: `http://localhost:5173`

La variable `VITE_API_URL` debe apuntar a `http://localhost:8000/api/v1`.

## Compilación de producción

```powershell
cd frontend
npm run build
```


## Fase 12 - Refactor CRUD administrativo
- Clientes con detalle, edición total, filtros, activación/inactivación y archivado seguro.
- Servicios, empleados y productos con crear, ver, editar, cambiar estado y eliminar según rol.
- Categorías de producto y proveedores ahora tienen actualización y eliminación segura en API.
- Menú administrativo filtrado por rol.
- ADMINISTRADOR puede eliminar; RECEPCIONISTA puede crear/editar/cambiar estado; ESTILISTA queda en modo consulta donde corresponde.

## Fase 13 - Portal del cliente

Esta versión incorpora el rol `CLIENTE` y un portal completamente separado del panel administrativo.

### Funciones del cliente
- Registro público de una cuenta vinculada automáticamente a su ficha de cliente.
- Inicio de sesión con JWT.
- Inicio personalizado.
- Consulta exclusiva de sus propias citas.
- Reserva de nuevas citas.
- Reprogramación de citas pendientes o confirmadas.
- Cancelación con motivo.
- Actualización de perfil, preferencias y alergias.
- Cambio de contraseña desde el módulo de autenticación.

### Migración requerida

```powershell
cd backend
venv\Scripts\activate
alembic upgrade head
python -m app.seed.run_seed
```

La migración `0004_phase13_client_portal` agrega `usuarios.cliente_id` y el rol `CLIENTE`.

## Fase 14 — Agenda avanzada por rol

- Administrador: agenda global, edición completa, cambios de estado, cancelación y eliminación.
- Recepcionista: crea, confirma, reprograma, cancela y marca inasistencia; no finaliza servicios ni elimina.
- Estilista: solo ve sus citas; puede iniciar, finalizar y marcar inasistencia en citas propias.
- Cliente: catálogo público autenticado, selección visual de servicios/profesional/horarios, reprogramación y cancelación de sus propias citas.
- El backend aplica el alcance por rol aunque se intente acceder manualmente a otra URL.

## Fase 15 — ERP comercial por roles

Esta versión agrega POS, vínculo cita-venta, cobros pendientes, caja financiera,
comisiones, auditoría, notificaciones y comprobantes PDF para clientes.

### Actualización desde Fase 14

```powershell
cd backend
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

En otra terminal:

```powershell
cd frontend
npm install
npm run dev
```

### Accesos por rol

- ADMINISTRADOR: POS, ventas, caja, comisiones, reportes y auditoría.
- RECEPCIONISTA: POS, ventas, caja y cobro de citas finalizadas.
- ESTILISTA: agenda propia y comisiones propias.
- CLIENTE: citas, perfil, compras y comprobantes PDF.

## Fase 19 - Experiencia premium y datos profesionales

Esta versión incorpora una vista de inventario más profesional y una carga completa de demostración coherente para todos los módulos.

### Reiniciar y cargar toda la base de datos

> **Advertencia:** el siguiente comando elimina toda la información actual de negocio y vuelve a cargar datos profesionales.

```powershell
cd backend
.\venv\Scripts\Activate.ps1
alembic upgrade head
python -m app.seed.professional_seed --confirm-reset
```

La carga incluye roles, usuarios internos, 15 clientes, 6 cuentas de portal, 21 servicios, 5 profesionales, 30 productos, 5 proveedores, inventario, kardex, citas, ventas, pagos, caja, comisiones, compras, promociones y configuración del salón.

### Credenciales

```text
Administrador: admin@salon.com / Admin123*
Recepción: recepcion@salon.com / Recepcion123*
Estilista: estilista@salon.com / Estilista123*
Cliente: camila.torres@demo.pe / Cliente123*
```

## Fase 20 Premium
Para reemplazar todos los datos anteriores y cargar el escenario profesional completo:

```powershell
cd backend
python -m app.seed.professional_seed --confirm-reset
```

El portal del cliente incluye catálogo visual, filtros, selección de servicios mediante tarjetas y reserva guiada.

## Corrección de incongruencias (revisión de mantenimiento)

Se auditó el proyecto completo cruzando backend (roles y rutas reales) contra frontend
(rutas, menú y permisos) y se corrigieron las siguientes incongruencias:

1. **Permisos de RECEPCIONISTA incompletos en el frontend.** El backend ya permitía a
   RECEPCIONISTA crear/editar productos, proveedores, compras y consultar reportes
   (`admin_recep` en `inventory_routes.py`, roles en `report_routes.py`), pero el router
   (`App.tsx`) y el menú lateral (`AppLayout.tsx`) limitaban `/inventario`, `/compras` y
   `/reportes` solo a ADMINISTRADOR. Se alinearon ambos con el backend.
2. **`CatalogPage.tsx` bloqueaba la edición a RECEPCIONISTA** (`canEdit` solo admitía
   ADMINISTRADOR) en Servicios y Empleados, contradiciendo la regla documentada en la
   Fase 12 y el patrón ya usado correctamente en `ClientsPage.tsx`. Se corrigió para que
   coincida con el resto del sistema.
3. **Código muerto/duplicado en `CatalogPage.tsx`.** Existía una configuración `products`
   completa (con su propio flujo PATCH/POST) que nunca se usaba: la ruta `/inventario`
   siempre renderiza `ProductsPage.tsx`. Mantener dos implementaciones del mismo módulo
   es una fuente típica de incongruencias futuras; se eliminó la duplicada.
4. **Parámetro de paginación mal escrito en `PurchasesPage.tsx`** (`tamanio` en vez de
   `tamano_pagina`): el backend lo ignoraba silenciosamente y siempre devolvía el tamaño
   de página por defecto. Corregido.
5. **Parámetro de paginación redundante en `CatalogPage.tsx`** (`tamano` y `tamano_pagina`
   enviados a la vez): se dejó únicamente el nombre real que espera la API.
6. **Versión inconsistente en el backend.** `main.py` declaraba `version="1.5.0"` en la
   app de FastAPI pero el endpoint raíz (`/`) devolvía `"version": "1.0.0"` escrito a mano.
   Ahora ambos leen el mismo valor.
7. **Credenciales reales en `backend/.env.example`.** El archivo de ejemplo (pensado para
   versionarse en git) traía una contraseña de base de datos con apariencia real en vez de
   un valor genérico. Se reemplazó por placeholders y una nota para generar `SECRET_KEY`
   de forma aleatoria por entorno. `backend/.env` real ya estaba correctamente excluido
   por `.gitignore`.
8. **Botón de eliminar visible para RECEPCIONISTA en `ProductsPage.tsx`.** Al abrir el
   acceso de esta pantalla a RECEPCIONISTA (punto 1), se ocultó el botón de eliminar
   producto para ese rol, ya que el backend restringe `DELETE /products` solo a
   ADMINISTRADOR — evita un botón que siempre terminaría en error 403.
9. **Bug real en la lógica de reserva: reprogramar una cita ocultaba el propio horario del
   cliente.** `AppointmentService.horarios_disponibles()` calculaba los horarios libres del
   profesional pero nunca excluía la cita que se estaba editando al buscar choques de
   horario. Resultado: cuando un cliente abría "Reprogramar" desde el portal, su hora
   actual siempre aparecía como ocupada (chocaba contra sí misma) y, si no había otros
   huecos ese día, no podía reprogramar en absoluto. Se corrigió en tres capas:
   - `AppointmentService.horarios_disponibles()` ahora acepta `excluir_cita_id` y lo pasa
     a `verificar_disponibilidad()`.
   - `GET /client-portal/catalog/available-slots` y `GET /appointments/available-slots`
     aceptan un parámetro opcional `cita_id`; el portal del cliente valida además que la
     cita pertenezca al cliente autenticado antes de excluirla.
   - `ClientAppointmentsPage.tsx` envía `cita_id: editing.id` al consultar horarios cuando
     el modal está en modo "Reprogramar", para que su propio horario vuelva a aparecer
     como disponible.

## Segunda ronda: lógica de reservas, vencimiento y datos de demostración

Se recibió una revisión adicional muy completa. Se verificó cada punto contra el código
real antes de aplicar cambios; algunos eran del **seed de demostración** (no afectan el
uso real de la app) y otros eran **bugs reales de la aplicación**. Estos últimos ya están
corregidos:

10. **Citas vencidas se quedaban "pendientes" para siempre.** Una cita PENDIENTE o
    CONFIRMADA cuya hora ya pasó seguía mostrando los botones "Reprogramar" y "Cancelar",
    porque tanto el frontend como el backend solo validaban el `estado`, nunca la fecha/hora.
    Se agregó `AppointmentService._vencer_si_corresponde()`: cada vez que se lee una cita
    (listado o detalle) y su hora de fin ya pasó sin haber cambiado de estado, se marca
    automáticamente como `NO_ASISTIO`. Como el frontend consume ese mismo estado, los
    botones de acción desaparecen solos sin necesidad de lógica de fechas duplicada en cada
    pantalla, y las reglas de transición de estado existentes (`TRANSICIONES`) ya impiden
    reprogramar o cancelar una cita que quedó en `NO_ASISTIO`.
11. **Se podían eliminar citas finalizadas o con venta asociada.** `DELETE /appointments/{id}`
    solo bloqueaba citas `EN_PROCESO`. Como la FK `ventas.cita_id` tiene `ON DELETE SET NULL`,
    borrar una cita con venta la desvinculaba silenciosamente del comprobante, perdiendo
    trazabilidad. Ahora se bloquea el borrado si la cita está `FINALIZADA` o tiene una venta
    vinculada, indicando que debe cancelarse en su lugar.
12. **Bug de zona horaria: la fecha "de hoy" se calculaba en UTC.** `new Date().toISOString().slice(0,10)`
    usa UTC, no la hora local del navegador. En Perú (UTC-5), pasadas las ~7:00 p. m. la
    agenda, el portal del cliente y los reportes ya mostraban el día siguiente como "hoy".
    Se creó `frontend/src/utils/date.ts` (`localToday()` / `localDaysAgo()`) y se reemplazó
    en `AgendaPage.tsx`, `ReceptionDashboardPage.tsx`, `ClientAppointmentsPage.tsx` y
    `ReportsPage.tsx`.
13. **El tipo `Appointment` en `types.ts` no correspondía a la API real.** Tenía
    `fecha_hora_inicio`/`fecha_hora_fin`/`observaciones`, campos que la API nunca devuelve
    (la API real usa `fecha`, `hora_inicio`, `hora_fin`, `notas`). No estaba importado en
    ninguna pantalla todavía, pero quedaba como una trampa para el próximo desarrollador
    que lo usara. Se corrigió para reflejar la forma real de `CitaResponse`.
14. **El portal del cliente mezclaba citas futuras, finalizadas y canceladas en una sola
    lista.** Se agregaron pestañas "Próximas / Historial / Canceladas" en
    `ClientAppointmentsPage.tsx` (filtrado en el cliente, sin cambios de API) para que no
    parezca que faltan citas al comparar con la vista filtrada por día de recepción.
15. **Confusión "el cliente ve muchas citas y recepción solo ve 2".** No era un error de
    datos: recepción filtra por un solo día en `AgendaPage.tsx`. Se aclaró el título y se
    agregó una nota explícita ("Vista por día") para que quede claro que es un filtro, no
    una pérdida de información.

### Pendientes identificados (fuera del alcance de esta ronda)

La revisión también señaló problemas reales pero de mayor alcance, que quedan como
siguientes pasos recomendados en vez de parches apresurados:

- **El seed de demostración (`professional_seed.py`) no reutiliza las reglas de negocio
  reales**: asigna servicios/empleados por índice cíclico sin validar que el empleado
  esté habilitado para ese servicio, genera ventas con servicios y fechas independientes
  de la cita real, y agrupa movimientos de caja de varios días en una sola sesión. Esto
  ensucia los datos de demostración pero **no afecta el comportamiento de la aplicación
  en uso real** (crear una cita o una venta desde la interfaz sí pasa por todas las
  validaciones). Recomendado: reescribir el seed para que cree cada cita/venta llamando a
  los mismos `AppointmentService`/`SaleService` que usa la API, en vez de insertar filas
  directamente.
- **Calendario día/semana/mes para recepción**: hoy es una lista filtrada por un solo día;
  falta una vista de calendario visual con semana/mes y por profesional.
- **Estado comercial independiente del operativo** (pendiente de cobro / pagada / anulada)
  para poder saber si una cita `FINALIZADA` ya se cobró sin mezclarlo con el flujo de
  atención.
- **Módulo administrativo de pedidos de la tienda**: el cliente puede pedir productos,
  pero no existe pantalla para que recepción/administración confirme, prepare, despache o
  convierta esos pedidos en venta; tampoco se reserva stock al crear el pedido (dos
  clientes podrían comprar la última unidad al mismo tiempo).
- **"Reprogramar" permite cambiar servicios y profesional, no solo fecha/hora**: es una
  decisión de producto pendiente de definir (¿separar en "Reprogramar" vs "Modificar
  reserva completa"?) más que un bug.

## Tercera ronda: cierre de caja devolvía 422

16. **`POST /cash/close` siempre fallaba con 422.** `CashPage.tsx` enviaba
    `{ monto_real, observaciones }`, pero el backend (`CajaCerrarRequest` en
    `sale_schema.py`) espera `{ monto_cierre_declarado, observaciones }`. Al no llegar
    `monto_cierre_declarado` (campo obligatorio), FastAPI rechazaba la petición antes de
    tocar la base de datos — por eso el log mostraba `ROLLBACK` seguido de `422` sin
    ningún error de PostgreSQL. Se corrigió el nombre del campo y, de paso, se reemplazó
    el `prompt()` del navegador (poco profesional y sin validación) por un modal
    consistente con el resto del sistema, con validación de monto antes de enviar.
17. **La tarjeta "Pagada" de Comisiones (vista ADMINISTRADOR) siempre mostraba S/ 0.00.**
    `GET /finance/commissions` solo devolvía `monto_total` (la suma de TODAS las
    comisiones, pagadas y pendientes mezcladas), sin desglosar `pendiente`/`pagada` como
    sí hacía correctamente `GET /finance/commissions/my` (vista ESTILISTA). El frontend ya
    esperaba esos dos campos (`data?.pendiente`, `data?.pagada`); al no existir en la
    respuesta del admin, "Pendiente" terminaba mostrando el total general en vez de solo
    lo pendiente, y "Pagada" quedaba fija en S/ 0.00 sin importar cuántas comisiones se
    pagaran. Se corrigió el endpoint para calcular y devolver ambos montos por separado.

## Cuarta ronda

18. **Módulo de Caja retirado del frontend.** Por decisión de producto se ocultaron los
    botones "Caja" y "Compras" del menú lateral (`AppLayout.tsx`). En el backend, el
    requisito de tener una caja abierta para registrar pagos en efectivo también se quitó
    de `SaleService.crear()`, así que las ventas en efectivo ya no dependen de este módulo.
19. **El estilista no podía marcar "No asistió" en una cita todavía sin confirmar.**
    `AgendaPage.tsx` muestra ese botón tanto para citas `PENDIENTE` como `CONFIRMADA`, pero
    `PATCH /appointments/{id}/status` solo permitía esa transición desde `CONFIRMADA` para
    el rol ESTILISTA — daba 409 con el mensaje "El estilista solo puede iniciar, finalizar
    o marcar inasistencia", que contradecía lo que la persona intentaba hacer. Se agregó
    `PENDIENTE → NO_ASISTIO` al mapa de transiciones permitidas para ESTILISTA, en línea
    con lo que ya permite la máquina de estados general (`TRANSICIONES`) usada por
    administración/recepción.
20. **Los pedidos de la tienda del cliente (pago en salón) eran invisibles para
    recepción/administración.** El cliente podía comprar productos desde el portal y ver
    sus propios pedidos, pero no existía ningún endpoint para que el staff los viera o
    los gestionara — el panel de recepción ni siquiera los mencionaba. Se agregó:
    - `GET /online-orders` y `PATCH /online-orders/{id}/status` (ADMINISTRADOR y
      RECEPCIONISTA) con una máquina de estados simple:
      `PENDIENTE → CONFIRMADO → LISTO → ENTREGADO`, con `CANCELADO` como salida en
      cualquier punto antes de entregar.
    - Página nueva `OnlineOrdersPage.tsx` en `/pedidos` para ver y avanzar cada pedido.
    - El widget roto de "Estado de caja" en el panel de recepción (dejó de funcionar al
      quitar el módulo de caja) se reemplazó por un widget real de "Pedidos de la
      tienda" con el conteo de pedidos por atender.
21. **Se terminó de retirar el módulo de Caja.** Además de ocultar los botones del menú
    (ronda anterior), se quitó la ruta `/caja`, el archivo `CashPage.tsx` y las
    referencias rotas a `/cash/current` que quedaban colgando en el panel de recepción.
22. **El CRUD de Compras estaba incompleto: solo Listar, sin Crear.** `PurchasesPage.tsx`
    mostraba la tabla de compras pero no tenía ningún botón ni formulario para registrar
    una compra nueva, aunque `POST /purchases` ya existía y funcionaba en el backend
    (suma stock, registra kardex y actualiza el costo del producto). Se reescribió la
    página completa: selector de proveedor, agregar productos con cantidad/costo/descuento
    por línea, descuento e impuesto globales, total calculado en vivo, y una vista de
    detalle por compra. De paso se restauró "Compras" en el menú lateral, que había
    quedado oculto en la ronda anterior junto con Caja.
23. **Verificación end-to-end del flujo de pedidos de la tienda + un bug de caché.**
    Se confirmó línea por línea que el flujo completo funciona: cliente compra en
    `ClientShopPage` → `POST /client-portal/orders` crea el pedido en `PENDIENTE` →
    `GET /online-orders` (backend) lo expone a ADMINISTRADOR/RECEPCIONISTA → aparece en
    el menú "Pedidos" y en el widget del panel de recepción, ambos visibles para
    RECEPCIONISTA. Al revisarlo a fondo apareció un bug real: el widget del panel de
    recepción usaba una `queryKey` de caché distinta (`['reception-online-orders']`) a la
    que usa `OnlineOrdersPage` (`['online-orders', filtro]`), así que al aceptar/avanzar
    un pedido desde `/pedidos`, el contador del panel de recepción no se refrescaba solo
    — quedaba desactualizado hasta recargar la página. Se unificó la `queryKey` para que
    ambas pantallas compartan el mismo prefijo de caché y se invaliden juntas.

## Página principal pública

24. **Se agregó una página de inicio pública (landing) antes del login.** Antes, entrar a
    `/` sin sesión te mandaba directo a `/login` — no había ninguna página de presentación
    del salón. Se creó `LandingPage.tsx`: página estática (sin llamadas a la API), con
    header, hero, sección "Nosotros", servicios destacados, contacto/ubicación y footer,
    en el mismo lenguaje visual del resto de la app (gradiente violeta/fucsia, marca
    "Elegance"). Botones "Iniciar sesión" y "Crear cuenta y reservar" llevan a `/login` y
    `/registro-cliente`. La ruta `/` ahora muestra la landing cuando NO hay sesión iniciada,
    y el panel de siempre (dashboard/agenda/etc.) cuando sí la hay — no se movió ninguna
    ruta interna, solo se intercambia qué se muestra en `/` según el estado de sesión.
25. **Servicios y productos de la landing ahora vienen del backend real.** Se agregaron
    `GET /public/services` y `GET /public/products` (sin login, solo datos no sensibles:
    nombre, precio, imagen, categoría) y se conectaron a la landing con `useQuery`, con
    estados de carga y de "todavía no hay nada publicado". Antes los servicios de la
    landing eran una lista fija en el código.
26. **Asistente virtual (chat con IA).** Se agregó `POST /public/chat`, un proxy hacia la
    API de Anthropic — la clave (`ANTHROPIC_API_KEY`) vive únicamente en
    `backend/.env`, nunca en el frontend. El asistente está acotado a nada más
    recomendar/aconsejar sobre el catálogo REAL de servicios (se arma el prompt con la
    lista de servicios activos leída de la base de datos en cada consulta, para que nunca
    invente un servicio o precio que no existe). Soporta adjuntar una foto: si el cliente
    manda una imagen, el modelo la analiza y recomienda cuál servicio del catálogo le
    conviene. Sin `ANTHROPIC_API_KEY` configurada, el chat responde con un mensaje claro
    de "no está activado" en vez de fallar feo. Para activarlo: genera una clave en
    https://console.anthropic.com y pégala en `backend/.env` (`ANTHROPIC_API_KEY=...`).
27. **El asistente no veía los productos, solo los servicios.** Buena pregunta la que
    hiciste — al revisar, el prompt (`_system_prompt`) solo armaba la lista con
    `_servicios_activos(db)`; los productos de la tienda nunca se le pasaban, así que no
    podía recomendarlos aunque existieran. Se agregó `_productos_activos(db)` (mismo query
    que usa `/public/products`) y ahora el prompt incluye **ambas** listas reales
    (servicios y productos), y las reglas se actualizaron para que recomiende lo que
    corresponda de cualquiera de las dos, incluso a partir de una foto.

## Flujo completo "Ver más" → crear cuenta → reservar/comprar

28. **Botón "Ver más" en cada tarjeta de servicio/producto de la landing.** Abre un modal
    con la descripción real, precio/duración y una imagen — todo desde los mismos
    endpoints públicos (`/public/services`, `/public/products`). Si el visitante no tiene
    sesión y quiere reservar o comprar, el botón lo manda a crear una cuenta.
29. **La cuenta nueva ya no te deja "botado" en la pantalla de inicio.** Antes, sin
    importar qué querías hacer, `ClientRegisterPage` siempre redirigía a `/cliente` a
    secas. Ahora el link de "Ver más" arma la URL con `?next=/cliente/agendar?servicio=ID`
    (para servicios) o `?next=/cliente/tienda` (para productos); tanto
    `ClientRegisterPage.tsx` como `LoginPage.tsx` leen ese `next` y, al terminar de crear
    la cuenta o iniciar sesión, te llevan directo a donde ibas — no hace falta buscarlo de
    nuevo. Por seguridad, solo se acepta un `next` que empiece con `/cliente` (nunca se
    usa para saltar a rutas administrativas).
30. **Bug real encontrado de paso: el login traía credenciales de ejemplo que no
    funcionan.** `LoginPage.tsx` precargaba `admin@peluqueria.com` / `Admin123.`, que no
    coincide con ninguna cuenta real del seed (`admin@salon.com` / `Admin123*`). Cualquiera
    que probara el sistema por primera vez con esos valores precargados obtenía un error
    de login. Se quitaron los valores precargados (campos vacíos con placeholder) y se
    referencia el README para las credenciales reales.

## Chatbot con memoria de sesión real + proveedor intercambiable (Anthropic / NVIDIA / n8n)

31. **Memoria de sesión de verdad (no solo en el navegador).** Antes, el historial del
    chat vivía únicamente en el estado de React: si recargabas la página, se perdía. Se
    creó la tabla `chat_mensajes` (migración `0007_chat_memory`), indexada por
    `sesion_id` — un UUID que el navegador genera una vez y guarda en `localStorage`
    (`getSesionId()` en `ChatWidget.tsx`). Cada mensaje (del usuario y del asistente) se
    guarda en la base de datos; al abrir el chat, `GET /public/chat/{sesion_id}` restaura
    la conversación completa. El backend arma el historial leyendo la base de datos, ya
    no depende de que el frontend reenvíe el historial en cada mensaje.
32. **El proveedor de IA ahora es intercambiable con una sola variable.** Se agregó
    `AI_PROVIDER` (`anthropic` | `nvidia` | `n8n`) en `backend/.env`. Los tres comparten
    exactamente el mismo prompt (armado con el catálogo real de servicios/productos) y la
    misma memoria de sesión; solo cambia a quién le pega el backend:
    - `anthropic` (por defecto): como antes, incluye análisis de imágenes.
    - `nvidia`: API de NIM (build.nvidia.com), compatible con OpenAI, tiene modelos
      gratuitos para probar. Esta integración no soporta imágenes todavía (avisa con un
      mensaje claro si se intenta).
    - `n8n`: el backend le hace `POST` a `N8N_WEBHOOK_URL` con
      `{sesion_id, mensaje, historial, system_prompt, imagen_base64, imagen_media_type}`
      y acepta la respuesta en cualquiera de estos campos: `respuesta`, `output`, `text`
      o `reply` (para no depender de cómo nombres el nodo final en tu flujo). Esto es el
      punto de enganche para armar ahí un pipeline propio (ej. clasificador + Groq),
      pero **n8n en sí es una herramienta externa que se instala y corre aparte** (Docker
      o `npm install -g n8n) — no es algo que viva dentro de este repositorio.
    - Sin ninguna clave configurada para el proveedor elegido, el chat responde con un
      mensaje claro de qué falta, en vez de fallar feo.
33. **Se agregó Groq como cuarto proveedor y se refactorizó el código repetido.**
    NVIDIA y Groq hablan el mismo formato de API (compatible con OpenAI), así que se
    extrajo un helper compartido `_llamar_openai_compatible()` (URL base, clave y modelo
    como parámetros) en vez de tener la misma lógica HTTP copiada dos veces — ahora
    `_llamar_nvidia()` y `_llamar_groq()` son wrappers de una línea sobre ese helper.
    Groq (`console.groq.com`) tiene registro simple con solo correo (sin la verificación
    de identidad que trababa el flujo de NVIDIA), plan gratis generoso y respuestas muy
    rápidas — buena alternativa si NVIDIA da problemas de cuenta. Se activa igual que
    los demás: `AI_PROVIDER=groq` + `GROQ_API_KEY` en `backend/.env`. Tampoco soporta
    imágenes (esa parte sigue siendo exclusiva de `anthropic`).
