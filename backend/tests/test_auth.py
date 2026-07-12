"""
Pruebas básicas del módulo de autenticación.
Requieren una base de datos PostgreSQL activa, migrada (`alembic upgrade head`)
y con el seed inicial cargado (`python -m app.seed.run_seed`), ya que validan
el login real contra el usuario administrador creado por el seed.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_con_credenciales_correctas_retorna_tokens():
    """Un login con las credenciales del admin sembrado debe retornar tokens JWT."""
    response = client.post(
        "/api/v1/auth/login", json={"correo": "admin@salon.com", "password": "Admin123*"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_con_password_incorrecto_retorna_401():
    """Un login con contraseña incorrecta debe retornar 401 Unauthorized."""
    response = client.post(
        "/api/v1/auth/login", json={"correo": "admin@salon.com", "password": "incorrecta"}
    )
    assert response.status_code == 401


def test_endpoint_me_sin_token_retorna_401():
    """El endpoint /me sin token de autenticación debe retornar 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_endpoint_me_con_token_retorna_perfil():
    """El endpoint /me con un token válido debe retornar el perfil del usuario."""
    login_response = client.post(
        "/api/v1/auth/login", json={"correo": "admin@salon.com", "password": "Admin123*"}
    )
    token = login_response.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["correo"] == "admin@salon.com"
    assert response.json()["rol"] == "ADMINISTRADOR"


def test_listar_usuarios_sin_permiso_de_admin_retorna_403():
    """Un usuario ESTILISTA no debe poder listar usuarios (solo ADMINISTRADOR puede)."""
    login_response = client.post(
        "/api/v1/auth/login", json={"correo": "estilista@salon.com", "password": "Estilista123*"}
    )
    token = login_response.json()["access_token"]

    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
