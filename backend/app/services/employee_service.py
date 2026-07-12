"""Lógica de negocio del módulo de empleados, horarios y ausencias."""
import uuid
from sqlalchemy.orm import Session
from app.core.constants import AccionAuditoria, EstadoGenerico
from app.core.exceptions import ConflictException, NotFoundException
from app.models.employee_model import Empleado, EmpleadoServicio, HorarioEmpleado, VacacionEmpleado, BloqueoHorario
from app.models.service_model import Servicio
from app.models.user_model import Usuario
from app.repositories.implementations.empleado_repository import EmpleadoRepository
from app.schemas.employee_schema import *
from app.services.audit_service import registrar_auditoria

class EmployeeService:
    def __init__(self, db: Session): self.db, self.repo = db, EmpleadoRepository(db)

    def listar(self, *args): return self.repo.listar(*args)

    def obtener(self, empleado_id):
        e = self.repo.obtener_por_id(empleado_id)
        if not e: raise NotFoundException("El empleado solicitado no existe")
        return e

    def _validar_unicos(self, documento=None, correo=None, usuario_id=None, empleado_id=None):
        for valor, getter, mensaje in [
            (documento, self.repo.obtener_por_documento, "Ya existe un empleado con ese documento"),
            (correo, self.repo.obtener_por_correo, "Ya existe un empleado con ese correo"),
            (usuario_id, self.repo.obtener_por_usuario, "La cuenta de usuario ya está vinculada a otro empleado")]:
            if valor:
                actual = getter(valor)
                if actual and actual.id != empleado_id: raise ConflictException(mensaje)
        if usuario_id and not self.db.query(Usuario).filter(Usuario.id == usuario_id).first():
            raise NotFoundException("El usuario seleccionado no existe")

    def _servicios(self, ids):
        ids = list(dict.fromkeys(ids or []))
        if not ids: return []
        servicios = self.db.query(Servicio).filter(Servicio.id.in_(ids), Servicio.estado == EstadoGenerico.ACTIVO).all()
        if len(servicios) != len(ids): raise ConflictException("Uno o más servicios no existen o están inactivos")
        return servicios

    def crear(self, datos: EmpleadoCrearRequest, actor: Usuario):
        self._validar_unicos(datos.documento, str(datos.correo) if datos.correo else None, datos.usuario_id)
        payload = datos.model_dump(exclude={"servicio_ids"})
        if payload.get("correo"): payload["correo"] = str(payload["correo"])
        e = Empleado(**payload, estado=EstadoGenerico.ACTIVO)
        self.repo.guardar(e)
        for s in self._servicios(datos.servicio_ids): e.servicios.append(EmpleadoServicio(servicio=s))
        registrar_auditoria(self.db, actor.id, AccionAuditoria.CREAR, "EMPLEADOS", "Empleado", str(e.id), valor_nuevo={"nombre": e.nombre_completo})
        self.db.commit(); return self.obtener(e.id)

    def actualizar(self, empleado_id, datos: EmpleadoActualizarRequest, actor: Usuario):
        e = self.obtener(empleado_id); cambios = datos.model_dump(exclude_unset=True); servicio_ids = cambios.pop("servicio_ids", None)
        self._validar_unicos(cambios.get("documento", e.documento), str(cambios.get("correo")) if cambios.get("correo") else e.correo, cambios.get("usuario_id", e.usuario_id), e.id)
        anterior = {k: str(getattr(e, k)) for k in cambios}
        for k, v in cambios.items(): setattr(e, k, str(v) if k == "correo" and v else v)
        if servicio_ids is not None:
            e.servicios.clear(); self.db.flush()
            for s in self._servicios(servicio_ids): e.servicios.append(EmpleadoServicio(servicio=s))
        registrar_auditoria(self.db, actor.id, AccionAuditoria.EDITAR, "EMPLEADOS", "Empleado", str(e.id), anterior, {k: str(v) for k,v in cambios.items()})
        self.db.commit(); return self.obtener(e.id)

    def cambiar_estado(self, empleado_id, estado, actor):
        e=self.obtener(empleado_id); anterior=e.estado; e.estado=estado
        registrar_auditoria(self.db, actor.id, AccionAuditoria.EDITAR, "EMPLEADOS", "Empleado", str(e.id), {"estado":anterior},{"estado":estado})
        self.db.commit(); return self.obtener(e.id)

    def eliminar(self, empleado_id, actor):
        e=self.obtener(empleado_id); e.estado=EstadoGenerico.INACTIVO
        registrar_auditoria(self.db, actor.id, AccionAuditoria.ELIMINAR, "EMPLEADOS", "Empleado", str(e.id), valor_anterior={"nombre":e.nombre_completo})
        self.db.commit()

    def guardar_horario(self, empleado_id, datos, actor):
        self.obtener(empleado_id)
        h=self.db.query(HorarioEmpleado).filter_by(empleado_id=empleado_id,dia_semana=datos.dia_semana).first()
        if not h: h=HorarioEmpleado(empleado_id=empleado_id, **datos.model_dump()); self.db.add(h)
        else:
            for k,v in datos.model_dump().items(): setattr(h,k,v)
        self.db.commit(); self.db.refresh(h); return h

    def agregar_vacacion(self, empleado_id, datos, actor):
        self.obtener(empleado_id)
        choque=self.db.query(VacacionEmpleado).filter(VacacionEmpleado.empleado_id==empleado_id, VacacionEmpleado.fecha_inicio<=datos.fecha_fin, VacacionEmpleado.fecha_fin>=datos.fecha_inicio).first()
        if choque: raise ConflictException("El periodo se cruza con otra vacación registrada")
        v=VacacionEmpleado(empleado_id=empleado_id, **datos.model_dump()); self.db.add(v); self.db.commit(); self.db.refresh(v); return v

    def agregar_bloqueo(self, empleado_id, datos, actor):
        self.obtener(empleado_id)
        choque=self.db.query(BloqueoHorario).filter(BloqueoHorario.empleado_id==empleado_id, BloqueoHorario.fecha==datos.fecha, BloqueoHorario.hora_inicio<datos.hora_fin, BloqueoHorario.hora_fin>datos.hora_inicio).first()
        if choque: raise ConflictException("El bloqueo se cruza con otro bloqueo existente")
        b=BloqueoHorario(empleado_id=empleado_id, **datos.model_dump()); self.db.add(b); self.db.commit(); self.db.refresh(b); return b
