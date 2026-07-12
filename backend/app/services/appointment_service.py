"""Lógica de negocio de agenda, disponibilidad y citas."""
import uuid
from datetime import datetime, timedelta, date, time
from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.constants import EstadoCita, EstadoGenerico, AccionAuditoria
from app.core.exceptions import NotFoundException, ConflictException, ScheduleConflictException, ValidationException
from app.models.appointment_model import Cita, CitaServicio
from app.models.client_model import Cliente
from app.models.employee_model import Empleado, EmpleadoServicio, HorarioEmpleado, VacacionEmpleado, BloqueoHorario
from app.models.service_model import Servicio
from app.models.user_model import Usuario
from app.repositories.implementations.cita_repository import CitaRepository
from app.services.audit_service import registrar_auditoria

ESTADOS_BLOQUEANTES = [EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA, EstadoCita.EN_PROCESO]
TRANSICIONES = {
    EstadoCita.PENDIENTE: {EstadoCita.CONFIRMADA, EstadoCita.CANCELADA, EstadoCita.NO_ASISTIO},
    EstadoCita.CONFIRMADA: {EstadoCita.EN_PROCESO, EstadoCita.CANCELADA, EstadoCita.NO_ASISTIO},
    EstadoCita.EN_PROCESO: {EstadoCita.FINALIZADA, EstadoCita.CANCELADA},
    EstadoCita.FINALIZADA: set(), EstadoCita.CANCELADA: set(), EstadoCita.NO_ASISTIO: set(),
}

class AppointmentService:
    def __init__(self, db: Session): self.db, self.repo = db, CitaRepository(db)

    def _vencer_si_corresponde(self, citas):
        """Fase de mantenimiento: una cita PENDIENTE/CONFIRMADA cuya hora de fin ya pasó
        no debe seguir mostrándose como accionable (reprogramar/cancelar/confirmar).
        Se marca automáticamente como NO_ASISTIO al momento de leerla."""
        ahora = datetime.now()
        cambiadas = False
        for c in citas:
            if c.estado in (EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA):
                fin = datetime.combine(c.fecha, c.hora_fin)
                if fin < ahora:
                    c.estado = EstadoCita.NO_ASISTIO
                    c.motivo_cancelacion = c.motivo_cancelacion or "Vencida automáticamente: la hora programada pasó sin registrar asistencia"
                    cambiadas = True
        if cambiadas:
            self.db.commit()
        return citas

    def listar(self, *args):
        items, total = self.repo.listar(*args)
        self._vencer_si_corresponde(items)
        return items, total

    def obtener(self, cita_id):
        cita = self.repo.obtener_por_id(cita_id)
        if not cita: raise NotFoundException("La cita solicitada no existe")
        self._vencer_si_corresponde([cita])
        return cita

    def _cliente(self, cliente_id):
        cliente = self.db.query(Cliente).filter(Cliente.id == cliente_id, Cliente.estado == EstadoGenerico.ACTIVO).first()
        if not cliente: raise NotFoundException("El cliente no existe o está inactivo")
        return cliente

    def _empleado(self, empleado_id):
        empleado = self.db.query(Empleado).filter(Empleado.id == empleado_id, Empleado.estado == EstadoGenerico.ACTIVO).first()
        if not empleado: raise NotFoundException("El empleado no existe o está inactivo")
        return empleado

    def _servicios(self, servicio_ids, empleado_id):
        ids = list(dict.fromkeys(servicio_ids or []))
        servicios = self.db.query(Servicio).filter(Servicio.id.in_(ids), Servicio.estado == EstadoGenerico.ACTIVO).all()
        if len(servicios) != len(ids): raise NotFoundException("Uno o más servicios no existen o están inactivos")
        asignados = {x.servicio_id for x in self.db.query(EmpleadoServicio).filter(EmpleadoServicio.empleado_id == empleado_id, EmpleadoServicio.servicio_id.in_(ids)).all()}
        if asignados != set(ids): raise ConflictException("El empleado no está habilitado para realizar todos los servicios seleccionados")
        return servicios

    @staticmethod
    def _sumar_minutos(hora: time, minutos: int):
        return (datetime.combine(date.today(), hora) + timedelta(minutes=minutos)).time()

    def verificar_disponibilidad(self, empleado_id, fecha, hora_inicio, hora_fin, excluir_cita_id=None):
        self._empleado(empleado_id)
        horario = self.db.query(HorarioEmpleado).filter_by(empleado_id=empleado_id, dia_semana=fecha.isoweekday()).first()
        if not horario or horario.es_dia_libre:
            return False, "El empleado no trabaja ese día"
        if hora_inicio < horario.hora_entrada or hora_fin > horario.hora_salida:
            return False, "La cita está fuera del horario laboral"
        if horario.hora_inicio_descanso and horario.hora_fin_descanso and hora_inicio < horario.hora_fin_descanso and hora_fin > horario.hora_inicio_descanso:
            return False, "La cita se cruza con el descanso del empleado"
        vacacion = self.db.query(VacacionEmpleado).filter(VacacionEmpleado.empleado_id==empleado_id, VacacionEmpleado.aprobado.is_(True), VacacionEmpleado.fecha_inicio<=fecha, VacacionEmpleado.fecha_fin>=fecha).first()
        if vacacion: return False, "El empleado está de vacaciones"
        bloqueo = self.db.query(BloqueoHorario).filter(BloqueoHorario.empleado_id==empleado_id, BloqueoHorario.fecha==fecha, BloqueoHorario.hora_inicio<hora_fin, BloqueoHorario.hora_fin>hora_inicio).first()
        if bloqueo: return False, "El horario se encuentra bloqueado"
        query = self.db.query(Cita).filter(Cita.empleado_id==empleado_id, Cita.fecha==fecha, Cita.estado.in_(ESTADOS_BLOQUEANTES), Cita.hora_inicio<hora_fin, Cita.hora_fin>hora_inicio)
        if excluir_cita_id: query = query.filter(Cita.id != excluir_cita_id)
        if query.first(): return False, "Existe otra cita en ese horario"
        return True, None

    def _programacion(self, empleado_id, fecha, hora_inicio, servicio_ids, excluir_cita_id=None):
        if fecha < date.today(): raise ValidationException("No se puede agendar una cita en una fecha pasada")
        servicios = self._servicios(servicio_ids, empleado_id)
        duracion = sum(s.duracion_minutos for s in servicios)
        precio = sum((s.precio for s in servicios), Decimal("0.00"))
        hora_fin = self._sumar_minutos(hora_inicio, duracion)
        disponible, motivo = self.verificar_disponibilidad(empleado_id, fecha, hora_inicio, hora_fin, excluir_cita_id)
        if not disponible: raise ScheduleConflictException(motivo)
        return servicios, duracion, precio, hora_fin


    def resumen(self, fecha, empleado_id=None):
        query = self.db.query(Cita).filter(Cita.fecha == fecha)
        if empleado_id:
            query = query.filter(Cita.empleado_id == empleado_id)
        estados = [x.estado for x in query.all()]
        from app.schemas.appointment_schema import ResumenAgendaResponse
        return ResumenAgendaResponse(
            fecha=fecha, total_citas=len(estados),
            pendientes=estados.count(EstadoCita.PENDIENTE),
            confirmadas=estados.count(EstadoCita.CONFIRMADA),
            en_proceso=estados.count(EstadoCita.EN_PROCESO),
            finalizadas=estados.count(EstadoCita.FINALIZADA),
            canceladas=estados.count(EstadoCita.CANCELADA),
            no_asistio=estados.count(EstadoCita.NO_ASISTIO),
        )

    def horarios_disponibles(self, empleado_id, fecha, servicio_ids, intervalo=30, excluir_cita_id=None):
        empleado = self._empleado(empleado_id)
        servicios = self._servicios(servicio_ids, empleado_id)
        duracion = sum(x.duracion_minutos for x in servicios)
        horario = self.db.query(HorarioEmpleado).filter_by(
            empleado_id=empleado.id, dia_semana=fecha.isoweekday()).first()
        if not horario or horario.es_dia_libre:
            return []
        resultado = []
        actual = horario.hora_entrada
        while True:
            fin = self._sumar_minutos(actual, duracion)
            if fin > horario.hora_salida or fin <= actual:
                break
            disponible, _ = self.verificar_disponibilidad(empleado_id, fecha, actual, fin, excluir_cita_id)
            if disponible:
                from app.schemas.appointment_schema import HorarioDisponibleResponse
                resultado.append(HorarioDisponibleResponse(hora_inicio=actual, hora_fin=fin))
            actual = self._sumar_minutos(actual, intervalo)
            if actual <= horario.hora_entrada:
                break
        return resultado

    def crear(self, datos, actor: Usuario):
        self._cliente(datos.cliente_id); self._empleado(datos.empleado_id)
        servicios, duracion, precio, hora_fin = self._programacion(datos.empleado_id, datos.fecha, datos.hora_inicio, datos.servicio_ids)
        cita = Cita(cliente_id=datos.cliente_id, empleado_id=datos.empleado_id, fecha=datos.fecha,
                    hora_inicio=datos.hora_inicio, hora_fin=hora_fin, duracion_total_minutos=duracion,
                    precio_total=precio, estado=EstadoCita.PENDIENTE, notas=datos.notas,
                    created_by=actor.id, updated_by=actor.id)
        self.repo.guardar(cita)
        for s in servicios: cita.servicios.append(CitaServicio(servicio=s, precio_aplicado=s.precio, duracion_aplicada_minutos=s.duracion_minutos))
        registrar_auditoria(self.db, actor.id, AccionAuditoria.CREAR, "CITAS", "Cita", str(cita.id), valor_nuevo={"fecha":str(cita.fecha),"hora":str(cita.hora_inicio)})
        self.db.commit(); return self.obtener(cita.id)

    def actualizar(self, cita_id, datos, actor):
        cita = self.obtener(cita_id)
        if cita.estado not in [EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA]: raise ConflictException("Solo se pueden editar citas pendientes o confirmadas")
        cambios = datos.model_dump(exclude_unset=True)
        cliente_id = cambios.get("cliente_id", cita.cliente_id); empleado_id = cambios.get("empleado_id", cita.empleado_id)
        fecha = cambios.get("fecha", cita.fecha); hora_inicio = cambios.get("hora_inicio", cita.hora_inicio)
        servicio_ids = cambios.get("servicio_ids", [x.servicio_id for x in cita.servicios])
        self._cliente(cliente_id); self._empleado(empleado_id)
        servicios, duracion, precio, hora_fin = self._programacion(empleado_id, fecha, hora_inicio, servicio_ids, cita.id)
        anterior={"fecha":str(cita.fecha),"hora":str(cita.hora_inicio),"empleado_id":str(cita.empleado_id)}
        cita.cliente_id=cliente_id; cita.empleado_id=empleado_id; cita.fecha=fecha; cita.hora_inicio=hora_inicio; cita.hora_fin=hora_fin
        cita.duracion_total_minutos=duracion; cita.precio_total=precio; cita.updated_by=actor.id
        if "notas" in cambios: cita.notas=cambios["notas"]
        cita.servicios.clear(); self.db.flush()
        for s in servicios: cita.servicios.append(CitaServicio(servicio=s, precio_aplicado=s.precio, duracion_aplicada_minutos=s.duracion_minutos))
        registrar_auditoria(self.db, actor.id, AccionAuditoria.EDITAR, "CITAS", "Cita", str(cita.id), anterior, {"fecha":str(fecha),"hora":str(hora_inicio),"empleado_id":str(empleado_id)})
        self.db.commit(); return self.obtener(cita.id)

    def cambiar_estado(self, cita_id, estado, motivo, actor):
        cita=self.obtener(cita_id)
        if estado == cita.estado: return cita
        if estado not in TRANSICIONES.get(cita.estado,set()): raise ConflictException(f"No se puede cambiar una cita de {cita.estado} a {estado}")
        anterior=cita.estado; cita.estado=estado; cita.updated_by=actor.id
        if estado==EstadoCita.CANCELADA: cita.motivo_cancelacion=motivo
        accion=AccionAuditoria.CANCELAR if estado==EstadoCita.CANCELADA else AccionAuditoria.EDITAR
        registrar_auditoria(self.db, actor.id, accion, "CITAS", "Cita", str(cita.id), {"estado":anterior},{"estado":estado})
        self.db.commit(); return self.obtener(cita.id)

    def eliminar(self, cita_id, actor):
        cita=self.obtener(cita_id)
        if cita.estado == EstadoCita.EN_PROCESO: raise ConflictException("No se puede eliminar una cita en proceso")
        from app.models.sale_model import Venta
        tiene_venta = self.db.query(Venta.id).filter(Venta.cita_id == cita_id).first() is not None
        if tiene_venta or cita.estado == EstadoCita.FINALIZADA:
            raise ConflictException("No se puede eliminar una cita finalizada o con una venta asociada; cancélela en su lugar para conservar la trazabilidad")
        self.db.delete(cita); registrar_auditoria(self.db, actor.id, AccionAuditoria.ELIMINAR, "CITAS", "Cita", str(cita.id))
        self.db.commit()
