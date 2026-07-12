# Instalación y ejecución en Windows

## Requisitos
- Python 3.11
- Node.js 20 o superior
- PostgreSQL 15 o superior

## 1. Crear la base de datos
En pgAdmin o psql crea:

```sql
CREATE USER peluqueria_user WITH PASSWORD 'Sinley123.';
CREATE DATABASE peluqueria OWNER peluqueria_user;
GRANT ALL PRIVILEGES ON DATABASE peluqueria TO peluqueria_user;
```

## 2. Preparar el backend
Abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m app.seed.professional_seed --confirm-reset
python run.py
```

Backend: http://localhost:8000
Swagger: http://localhost:8000/docs

## 3. Preparar el frontend
En otra terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Credenciales de demostración
- Administrador: admin@salon.com / Admin123*
- Recepción: recepcion@salon.com / Recepcion123*
- Estilista: estilista@salon.com / Estilista123*
- Cliente: camila.torres@demo.pe / Cliente123*

## Chat
El sistema viene con `AI_PROVIDER=local`, por lo que funciona sin Groq, Anthropic ni otra API externa. Si se configura un proveedor externo y falla, se usa automáticamente el asistente local.
