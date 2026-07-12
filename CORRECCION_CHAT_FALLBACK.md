# Corrección del chat 409

- El chat ya no devuelve 409 cuando AI_PROVIDER está configurado como groq, anthropic, nvidia o n8n y falta la clave.
- Ante cualquier fallo del proveedor externo, usa automáticamente el asistente local.
- Si se envía una imagen junto con una descripción, el modo local usa la descripción para recomendar servicios y productos reales.
- Para usar análisis visual real de fotografías todavía se necesita un proveedor compatible y su clave.
