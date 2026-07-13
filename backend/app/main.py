"""
Punto de entrada de la aplicación FastAPI.
Configura middlewares, CORS, manejo de excepciones y el registro de rutas.
Fase 7: se registran autenticación, usuarios, clientes, categorías y servicios.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth_routes import router as auth_router
from app.api.routes.user_routes import router as user_router
from app.api.routes.client_routes import router as client_router
from app.api.routes.service_routes import router as service_router
from app.api.routes.employee_routes import router as employee_router
from app.api.routes.appointment_routes import router as appointment_router
from app.api.routes.sale_routes import router as sale_router
from app.api.routes.inventory_routes import router as inventory_router
from app.api.routes.report_routes import router as report_router
from app.api.routes.client_portal_routes import router as client_portal_router
from app.api.routes.finance_routes import router as finance_router
from app.api.routes.public_routes import router as public_router
from app.core.config import settings
from app.core.error_handlers import register_exception_handlers

app = FastAPI(
    title=settings.APP_NAME,
    description="API REST para la gestión integral de un salón de belleza: "
    "clientes, empleados, citas, inventario, ventas, pagos, comisiones y reportes.",
    version="1.5.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS: permite que el frontend (Vite en localhost:5173) consuma la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejadores globales de excepciones
register_exception_handlers(app)


@app.get("/", tags=["Sistema"])
def raiz() -> dict:
    """Endpoint raíz de verificación rápida de que la API está activa."""
    return {
        "aplicacion": settings.APP_NAME,
        "estado": "activo",
        "version": app.version,
        "documentacion": "/docs",
    }


@app.get("/health", tags=["Sistema"])
def health_check() -> dict:
    """Endpoint de verificación de salud (health check) para monitoreo."""
    return {"status": "ok"}


# Registro de routers de negocio
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(user_router, prefix=settings.API_V1_PREFIX)
app.include_router(client_router, prefix=settings.API_V1_PREFIX)
app.include_router(service_router, prefix=settings.API_V1_PREFIX)
app.include_router(employee_router, prefix=settings.API_V1_PREFIX)
app.include_router(appointment_router, prefix=settings.API_V1_PREFIX)
app.include_router(sale_router, prefix=settings.API_V1_PREFIX)
app.include_router(inventory_router, prefix=settings.API_V1_PREFIX)
app.include_router(report_router, prefix=settings.API_V1_PREFIX)
app.include_router(client_portal_router, prefix=settings.API_V1_PREFIX)
app.include_router(finance_router, prefix=settings.API_V1_PREFIX)
app.include_router(public_router, prefix=settings.API_V1_PREFIX)


# Fase 9: dashboard, indicadores, reportes y exportaciones integrados.
@app.get("/cors-test")
def cors_test():
    return {
        "cors": settings.CORS_ORIGINS,
        "cors_list": settings.cors_origins_list,
    }