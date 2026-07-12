"""
Seed de roles del sistema.
Crea los tres roles fijos (ADMINISTRADOR, RECEPCIONISTA, ESTILISTA) si no existen.
"""
from sqlalchemy.orm import Session

from app.core.constants import RolesSistema
from app.models.role_model import Rol

DESCRIPCIONES_ROLES = {
    RolesSistema.ADMINISTRADOR: "Acceso total al sistema: usuarios, configuración, reportes y auditoría",
    RolesSistema.RECEPCIONISTA: "Gestión de clientes, citas, ventas y pagos",
    RolesSistema.ESTILISTA: "Gestión de su propia agenda, citas y comisiones",
    RolesSistema.CLIENTE: "Portal de autoservicio para reservar y administrar sus propias citas",
}


def seed_roles(db: Session) -> dict[str, Rol]:
    """
    Crea los roles base del sistema si aún no existen en la base de datos.

    Returns:
        Diccionario {nombre_rol: instancia Rol} con los tres roles disponibles.
    """
    roles: dict[str, Rol] = {}
    for nombre in RolesSistema.TODOS:
        rol_existente = db.query(Rol).filter(Rol.nombre == nombre).first()
        if rol_existente:
            roles[nombre] = rol_existente
            continue
        nuevo_rol = Rol(nombre=nombre, descripcion=DESCRIPCIONES_ROLES[nombre])
        db.add(nuevo_rol)
        db.flush()
        roles[nombre] = nuevo_rol
    db.commit()
    return roles
