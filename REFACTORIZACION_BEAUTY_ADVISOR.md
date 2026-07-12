# Refactorización Beauty Advisor

El chat ya no funciona como una búsqueda general por palabras. Ahora sigue este flujo:

1. Detecta si la consulta pertenece al negocio del salón.
2. Clasifica la intención: servicio, producto, reserva, consejo de belleza, imagen o aclaración.
3. Detecta el área: maquillaje, cabello, uñas, facial, cejas/pestañas, depilación, masajes o barbería.
4. Consulta únicamente servicios y productos activos de PostgreSQL.
5. Aplica ranking con penalización fuerte para categorías incompatibles.
6. Devuelve texto, tarjetas reales y botones de respuesta rápida.
7. Solo usa la IA externa para analizar imágenes; las consultas de texto responden localmente para ser rápidas.
8. Si el proveedor visual falla o tarda, responde con fallback local sin error 409.

## Ejemplo corregido

Consulta: `quiero un maquillaje`

Resultado esperado:
- Maquillaje Social
- Pack Novia Premium

No deben aparecer productos de barbería, manicure ni categorías ajenas.

## Archivos principales

- `backend/app/ai/intent_detector.py`
- `backend/app/ai/recommendation_engine.py`
- `backend/app/ai/response_builder.py`
- `backend/app/ai/beauty_assistant.py`
- `backend/app/api/routes/public_routes.py`
- `frontend/src/components/ChatWidget.tsx`

## Imágenes

El frontend acepta JPG, PNG y WEBP, comprime la imagen y la envía al backend. Para análisis visual configura Groq u otro proveedor compatible en `backend/.env`. Sin clave o ante un fallo, el chat continúa funcionando en modo local.
