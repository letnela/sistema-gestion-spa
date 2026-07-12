"""Rutas REST del módulo de categorías y servicios."""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.constants import RolesSistema
from app.core.permissions import require_roles
from app.database.session import get_db
from app.models.service_model import CategoriaServicio, Servicio
from app.models.user_model import Usuario
from app.schemas.common_schema import RespuestaExito, RespuestaMensaje, RespuestaPaginada
from app.schemas.service_schema import (
    CambiarEstadoRequest,
    CategoriaServicioActualizarRequest,
    CategoriaServicioCrearRequest,
    CategoriaServicioResponse,
    ServicioActualizarRequest,
    ServicioCrearRequest,
    ServicioResponse,
)
from app.services.service_service import CategoriaServicioService, ServicioService

router = APIRouter(prefix="/services", tags=["Servicios"], dependencies=[Depends(require_roles(
    RolesSistema.ADMINISTRADOR, RolesSistema.RECEPCIONISTA, RolesSistema.ESTILISTA
))])


def _categoria_response(categoria: CategoriaServicio) -> CategoriaServicioResponse:
    return CategoriaServicioResponse(
        id=categoria.id,
        nombre=categoria.nombre,
        descripcion=categoria.descripcion,
        estado=categoria.estado,
        cantidad_servicios=len(categoria.servicios),
        created_at=categoria.created_at,
        updated_at=categoria.updated_at,
    )


def _servicio_response(servicio: Servicio) -> ServicioResponse:
    return ServicioResponse(
        id=servicio.id,
        categoria_id=servicio.categoria_id,
        categoria_nombre=servicio.categoria.nombre,
        nombre=servicio.nombre,
        descripcion=servicio.descripcion,
        precio=servicio.precio,
        duracion_minutos=servicio.duracion_minutos,
        imagen_url=servicio.imagen_url,
        porcentaje_comision=servicio.porcentaje_comision,
        estado=servicio.estado,
        created_at=servicio.created_at,
        updated_at=servicio.updated_at,
    )


@router.get("/categories", response_model=RespuestaPaginada[CategoriaServicioResponse])
def listar_categorias(estado: str | None = Query(None), busqueda: str | None = Query(None),
                      pagina: int = Query(1, ge=1), tamano_pagina: int = Query(20, ge=1, le=100),
                      orden_por: str | None = Query("nombre"),
                      orden_direccion: str = Query("asc", pattern="^(asc|desc)$"),
                      db: Session = Depends(get_db)):
    items, total = CategoriaServicioService(db).listar(estado, busqueda, pagina,
                                                        tamano_pagina, orden_por,
                                                        orden_direccion)
    return RespuestaPaginada.crear([_categoria_response(c) for c in items], total,
                                    pagina, tamano_pagina)


@router.post("/categories", response_model=RespuestaExito[CategoriaServicioResponse], status_code=201,
             dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def crear_categoria(datos: CategoriaServicioCrearRequest,
                    actor: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    categoria = CategoriaServicioService(db).crear(datos, actor)
    return RespuestaExito(data=_categoria_response(categoria),
                          message="Categoría creada correctamente")


@router.get("/categories/{categoria_id}", response_model=RespuestaExito[CategoriaServicioResponse])
def obtener_categoria(categoria_id: uuid.UUID, db: Session = Depends(get_db)):
    return RespuestaExito(data=_categoria_response(CategoriaServicioService(db).obtener(categoria_id)))


@router.put("/categories/{categoria_id}", response_model=RespuestaExito[CategoriaServicioResponse],
            dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def actualizar_categoria(categoria_id: uuid.UUID, datos: CategoriaServicioActualizarRequest,
                         actor: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    categoria = CategoriaServicioService(db).actualizar(categoria_id, datos, actor)
    return RespuestaExito(data=_categoria_response(categoria),
                          message="Categoría actualizada correctamente")


@router.patch("/categories/{categoria_id}/status",
              response_model=RespuestaExito[CategoriaServicioResponse],
              dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def cambiar_estado_categoria(categoria_id: uuid.UUID, datos: CambiarEstadoRequest,
                             actor: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    categoria = CategoriaServicioService(db).cambiar_estado(categoria_id, datos.estado, actor)
    return RespuestaExito(data=_categoria_response(categoria),
                          message="Estado de categoría actualizado")


@router.delete("/categories/{categoria_id}", response_model=RespuestaMensaje,
               dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def eliminar_categoria(categoria_id: uuid.UUID, actor: Usuario = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    CategoriaServicioService(db).eliminar(categoria_id, actor)
    return RespuestaMensaje(message="Categoría eliminada correctamente")


@router.get("", response_model=RespuestaPaginada[ServicioResponse])
def listar_servicios(categoria_id: uuid.UUID | None = Query(None),
                     estado: str | None = Query(None), busqueda: str | None = Query(None),
                     precio_min: float | None = Query(None, ge=0),
                     precio_max: float | None = Query(None, ge=0),
                     pagina: int = Query(1, ge=1), tamano_pagina: int = Query(20, ge=1, le=100),
                     orden_por: str | None = Query("nombre"),
                     orden_direccion: str = Query("asc", pattern="^(asc|desc)$"),
                     db: Session = Depends(get_db)):
    items, total = ServicioService(db).listar(categoria_id, estado, busqueda,
                                              precio_min, precio_max, pagina,
                                              tamano_pagina, orden_por, orden_direccion)
    return RespuestaPaginada.crear([_servicio_response(s) for s in items], total,
                                    pagina, tamano_pagina)


@router.post("", response_model=RespuestaExito[ServicioResponse], status_code=201,
             dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def crear_servicio(datos: ServicioCrearRequest, actor: Usuario = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    servicio = ServicioService(db).crear(datos, actor)
    return RespuestaExito(data=_servicio_response(servicio),
                          message="Servicio creado correctamente")


@router.get("/{servicio_id}", response_model=RespuestaExito[ServicioResponse])
def obtener_servicio(servicio_id: uuid.UUID, db: Session = Depends(get_db)):
    return RespuestaExito(data=_servicio_response(ServicioService(db).obtener(servicio_id)))


@router.put("/{servicio_id}", response_model=RespuestaExito[ServicioResponse],
            dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def actualizar_servicio(servicio_id: uuid.UUID, datos: ServicioActualizarRequest,
                        actor: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    servicio = ServicioService(db).actualizar(servicio_id, datos, actor)
    return RespuestaExito(data=_servicio_response(servicio),
                          message="Servicio actualizado correctamente")


@router.patch("/{servicio_id}/status", response_model=RespuestaExito[ServicioResponse],
              dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def cambiar_estado_servicio(servicio_id: uuid.UUID, datos: CambiarEstadoRequest,
                            actor: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    servicio = ServicioService(db).cambiar_estado(servicio_id, datos.estado, actor)
    return RespuestaExito(data=_servicio_response(servicio),
                          message="Estado del servicio actualizado")


@router.delete("/{servicio_id}", response_model=RespuestaMensaje,
               dependencies=[Depends(require_roles(RolesSistema.ADMINISTRADOR))])
def eliminar_servicio(servicio_id: uuid.UUID, actor: Usuario = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    ServicioService(db).eliminar(servicio_id, actor)
    return RespuestaMensaje(message="Servicio eliminado correctamente")
