# Chat IA especializado en el salón

## Funcionalidad incluida

- El asistente solo responde temas relacionados con el salón: servicios, productos, citas y cuidados de belleza.
- Las preguntas ajenas al negocio se rechazan con una redirección amable.
- Acepta imágenes JPG, PNG y WEBP de hasta 8 MB.
- El frontend reduce la imagen a un máximo de 1280 px antes de enviarla para mejorar la velocidad.
- Con Groq configurado, usa un modelo visual para analizar la foto.
- Si Groq no está disponible, el sistema nunca devuelve 409: usa el asistente local y la descripción escrita.
- La respuesta contiene tarjetas de servicios y productos reales de la base de datos.
- Cada tarjeta muestra imagen, precio, duración o stock y botón Reservar/Comprar.

## Configuración para análisis visual con Groq

En `backend/.env` deja una sola configuración, sin líneas duplicadas:

```env
AI_PROVIDER=groq
GROQ_API_KEY=COLOCA_AQUI_TU_NUEVA_CLAVE
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_VISION_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct
CHAT_PROVIDER_TIMEOUT_SECONDS=8
CHAT_FAST_LOCAL_ENABLED=true
```

Reinicia el backend después de modificar `.env`. Nunca publiques ni compartas la API key.

## Prueba sugerida

1. Abre el chat.
2. Adjunta una fotografía del cabello.
3. Escribe: `Tengo el cabello seco y maltratado, ¿qué me recomiendas?`
4. El chat debe responder y mostrar tarjetas reales del catálogo.
5. Pregunta algo ajeno, por ejemplo sobre programación; el chat debe indicar que solo atiende asuntos del salón.
