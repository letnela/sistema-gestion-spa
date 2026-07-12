# Fase 21 — Experiencia premium responsive y tienda del cliente

## Portal del cliente
- Navegación de escritorio y navegación inferior tipo app en móvil.
- Diseño adaptable desde 320 px, tablet y escritorio.
- Catálogo visual de servicios con imágenes remotas configurables.
- Boutique de productos con búsqueda, categorías, stock y carrito persistente.
- Pedido online con recojo en salón o delivery, método de pago y seguimiento.
- Historial de pedidos del cliente.
- Estados, validaciones de stock y cancelación segura.

## Imágenes
Los seeds asignan URLs HTTPS de Unsplash a servicios y productos. Las imágenes son reemplazables desde los CRUD mediante `imagen_url`. El frontend incluye fallback visual si una URL falla.

## Migración
Ejecutar `alembic upgrade head` para crear `pedidos_online` y `pedido_online_detalles`.
