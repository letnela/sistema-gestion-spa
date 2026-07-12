# Instalación en Windows PowerShell

## Backend

```powershell
cd backend
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
python -m app.seed.professional_seed --confirm-reset
uvicorn app.main:app --reload
```

## Frontend

Abre otra terminal:

```powershell
cd frontend
npm config set registry https://registry.npmjs.org/
npm install --no-audit --no-fund
npm run dev
```

El proyecto incluye `.npmrc` con el registro público y un `package-lock.json` sin enlaces internos.

## Groq para imágenes

Usa una clave nueva y no la compartas:

```env
AI_PROVIDER=groq
GROQ_API_KEY=TU_CLAVE_NUEVA
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_VISION_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct
CHAT_PROVIDER_TIMEOUT_SECONDS=8
```
