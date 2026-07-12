"""
Pruebas básicas de la Fase 1: verifica que la aplicación FastAPI se
construye correctamente y que los endpoints de sistema responden.
Requiere que las dependencias de requirements.txt estén instaladas.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_raiz_responde_ok():
    """El endpoint raíz debe responder 200 y contener el nombre de la app."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["estado"] == "activo"
    assert "aplicacion" in body


def test_health_check_responde_ok():
    """El endpoint /health debe responder 200 con status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_swagger_disponible():
    """La documentación Swagger debe estar accesible en /docs."""
    response = client.get("/docs")
    assert response.status_code == 200
