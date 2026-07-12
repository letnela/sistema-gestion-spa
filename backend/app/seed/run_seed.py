"""
Script ejecutable que corre todos los seeds del sistema en el orden correcto:
1. Roles
2. Usuarios iniciales (admin, recepcionista, estilista)
3. Datos de demostración (clientes, empleados, servicios, productos, etc.)

Uso:
    python -m app.seed.run_seed
"""
from app.database.session import SessionLocal
from app.seed.admin_seed import seed_admin_and_base_users
from app.seed.demo_seed import run_demo_seed
from app.seed.roles_seed import seed_roles


def main() -> None:
    """Punto de entrada del script de seed."""
    db = SessionLocal()
    try:
        print("1/3 Creando roles...")
        roles = seed_roles(db)
        print(f"    Roles disponibles: {list(roles.keys())}")

        print("2/3 Creando usuarios iniciales...")
        usuarios = seed_admin_and_base_users(db, roles)
        print(f"    Usuarios disponibles: {list(usuarios.keys())}")

        print("3/3 Creando datos de demostración...")
        run_demo_seed(db)

        print("Seed completado exitosamente.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
