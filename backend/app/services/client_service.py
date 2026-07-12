"""Servicio de clientes y administración de acceso al portal."""
import secrets
import uuid
from sqlalchemy.orm import Session
from app.core.constants import AccionAuditoria, EstadoGenerico, RolesSistema
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.security import hash_password
from app.models.client_model import Cliente
from app.models.user_model import Usuario
from app.models.role_model import Rol
from app.repositories.implementations.cliente_repository import ClienteRepository
from app.schemas.client_schema import ClienteActualizarRequest, ClienteCrearRequest
from app.services.audit_service import registrar_auditoria

class ClientService:
    def __init__(self, db: Session):
        self.db=db; self.repo=ClienteRepository(db)

    def listar(self, estado, busqueda, pagina, tamano_pagina, orden_por, orden_direccion):
        return self.repo.listar(estado,busqueda,pagina,tamano_pagina,orden_por,orden_direccion)

    def obtener_por_id(self, cliente_id: uuid.UUID) -> Cliente:
        c=self.repo.obtener_por_id(cliente_id)
        if not c: raise NotFoundException("El cliente solicitado no existe")
        return c

    def usuario_portal(self, cliente_id: uuid.UUID) -> Usuario | None:
        return self.db.query(Usuario).filter(Usuario.cliente_id==cliente_id).first()

    def _validar_unicidad(self, documento, correo, cliente_id=None):
        if documento:
            x=self.repo.obtener_por_documento(documento)
            if x and x.id!=cliente_id: raise ConflictException(f"Ya existe un cliente con el documento {documento}")
        if correo:
            x=self.repo.obtener_por_correo(correo)
            if x and x.id!=cliente_id: raise ConflictException(f"Ya existe un cliente con el correo {correo}")

    def _rol_cliente(self) -> Rol:
        rol=self.db.query(Rol).filter(Rol.nombre==RolesSistema.CLIENTE).first()
        if not rol:
            rol=Rol(nombre=RolesSistema.CLIENTE,descripcion="Portal de autoservicio del cliente")
            self.db.add(rol); self.db.flush()
        return rol

    def crear_acceso_portal(self, cliente_id: uuid.UUID, password: str|None, actor: Usuario):
        c=self.obtener_por_id(cliente_id)
        if self.usuario_portal(c.id): raise ConflictException("Este cliente ya tiene acceso al portal")
        if not c.correo: raise ValidationException("El cliente necesita un correo para crear acceso al portal")
        correo=c.correo.lower().strip()
        existente=self.db.query(Usuario).filter(Usuario.correo==correo).first()
        if existente: raise ConflictException("Ya existe un usuario con el correo del cliente")
        temporal=password or (secrets.token_urlsafe(8)+"9a")
        u=Usuario(nombre_completo=c.nombre_completo,correo=correo,password_hash=hash_password(temporal),
                  rol_id=self._rol_cliente().id,cliente_id=c.id,telefono=c.telefono,
                  estado=EstadoGenerico.ACTIVO,debe_cambiar_password=password is None)
        self.db.add(u); self.db.flush()
        registrar_auditoria(self.db,actor.id,AccionAuditoria.CREAR,"CLIENTES","UsuarioPortal",str(u.id),
                            valor_nuevo={"cliente_id":str(c.id),"correo":correo})
        self.db.commit(); self.db.refresh(u)
        return u, temporal if password is None else None

    def crear(self, datos: ClienteCrearRequest, actor: Usuario) -> Cliente:
        documento=datos.documento.strip() if datos.documento else None
        correo=str(datos.correo).lower().strip() if datos.correo else None
        self._validar_unicidad(documento,correo)
        payload=datos.model_dump(exclude={"correo","documento","crear_acceso_portal","password_portal"})
        c=Cliente(**payload,documento=documento,correo=correo,estado=EstadoGenerico.ACTIVO,created_by=actor.id)
        self.db.add(c); self.db.flush()
        registrar_auditoria(self.db,actor.id,AccionAuditoria.CREAR,"CLIENTES","Cliente",str(c.id),valor_nuevo={"nombre":c.nombre_completo})
        if datos.crear_acceso_portal:
            if not correo: raise ValidationException("Debe indicar correo para crear acceso al portal")
            if self.db.query(Usuario).filter(Usuario.correo==correo).first(): raise ConflictException("Ya existe un usuario con ese correo")
            pwd=datos.password_portal or (secrets.token_urlsafe(8)+"9a")
            self.db.add(Usuario(nombre_completo=c.nombre_completo,correo=correo,password_hash=hash_password(pwd),
                rol_id=self._rol_cliente().id,cliente_id=c.id,telefono=c.telefono,estado=EstadoGenerico.ACTIVO,
                debe_cambiar_password=datos.password_portal is None))
        self.db.commit(); self.db.refresh(c); return c

    def actualizar(self, cliente_id, datos: ClienteActualizarRequest, actor: Usuario):
        c=self.obtener_por_id(cliente_id); cambios=datos.model_dump(exclude_unset=True)
        correo=str(cambios["correo"]).lower().strip() if cambios.get("correo") else cambios.get("correo")
        documento=cambios.get("documento")
        if isinstance(documento,str): documento=documento.strip() or None
        self._validar_unicidad(documento if "documento" in cambios else c.documento, correo if "correo" in cambios else c.correo,c.id)
        u=self.usuario_portal(c.id)
        if u and "correo" in cambios and correo!=u.correo:
            if not correo: raise ValidationException("No puede quitar el correo mientras el cliente tenga acceso al portal")
            dup=self.db.query(Usuario).filter(Usuario.correo==correo,Usuario.id!=u.id).first()
            if dup: raise ConflictException("El nuevo correo ya pertenece a otro usuario")
            u.correo=correo
        anterior={k:getattr(c,k) for k in cambios}
        if "correo" in cambios: cambios["correo"]=correo
        if "documento" in cambios: cambios["documento"]=documento
        for k,v in cambios.items(): setattr(c,k,v)
        if u:
            u.nombre_completo=c.nombre_completo; u.telefono=c.telefono
        c.updated_by=actor.id
        registrar_auditoria(self.db,actor.id,AccionAuditoria.EDITAR,"CLIENTES","Cliente",str(c.id),anterior,cambios)
        self.db.commit(); self.db.refresh(c); return c

    def cambiar_estado(self, cliente_id, estado, actor):
        c=self.obtener_por_id(cliente_id); anterior=c.estado; c.estado=estado; c.updated_by=actor.id
        u=self.usuario_portal(c.id)
        if u: u.estado=estado
        registrar_auditoria(self.db,actor.id,AccionAuditoria.EDITAR,"CLIENTES","Cliente",str(c.id),{"estado":anterior},{"estado":estado})
        self.db.commit(); self.db.refresh(c); return c

    def cambiar_estado_portal(self, cliente_id, estado, actor):
        u=self.usuario_portal(cliente_id)
        if not u: raise NotFoundException("El cliente no tiene acceso al portal")
        anterior=u.estado; u.estado=estado
        registrar_auditoria(self.db,actor.id,AccionAuditoria.EDITAR,"CLIENTES","UsuarioPortal",str(u.id),{"estado":anterior},{"estado":estado})
        self.db.commit(); self.db.refresh(u); return u

    def resetear_password_portal(self, cliente_id, actor):
        u=self.usuario_portal(cliente_id)
        if not u: raise NotFoundException("El cliente no tiene acceso al portal")
        pwd=secrets.token_urlsafe(8)+"9a"; u.password_hash=hash_password(pwd); u.debe_cambiar_password=True
        u.intentos_fallidos=0; u.bloqueado_hasta=None
        registrar_auditoria(self.db,actor.id,AccionAuditoria.EDITAR,"CLIENTES","UsuarioPortal",str(u.id),valor_nuevo={"accion":"reset_password"})
        self.db.commit(); return u,pwd

    def eliminar_acceso_portal(self, cliente_id, actor):
        u=self.usuario_portal(cliente_id)
        if not u: raise NotFoundException("El cliente no tiene acceso al portal")
        uid=str(u.id); self.db.delete(u)
        registrar_auditoria(self.db,actor.id,AccionAuditoria.ELIMINAR,"CLIENTES","UsuarioPortal",uid)
        self.db.commit()

    def eliminar(self, cliente_id, actor):
        c=self.obtener_por_id(cliente_id); c.eliminado=True; c.estado=EstadoGenerico.INACTIVO; c.updated_by=actor.id
        u=self.usuario_portal(c.id)
        if u: u.estado=EstadoGenerico.INACTIVO
        registrar_auditoria(self.db,actor.id,AccionAuditoria.ELIMINAR,"CLIENTES","Cliente",str(c.id),valor_anterior={"nombre":c.nombre_completo})
        self.db.commit()
