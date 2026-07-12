# Corrección de Compras e Inventario

## Cambios realizados

1. Los productos nuevos se crean siempre con stock 0.
2. La entrada de mercadería debe registrarse desde el módulo Compras.
3. Cada compra actualiza el stock, el último costo de compra y genera un movimiento ENTRADA en el kardex.
4. Si un producto no tiene proveedor, la primera compra le asigna el proveedor seleccionado.
5. Si el producto pertenece a otro proveedor, la compra se rechaza con un mensaje claro.
6. El catálogo público carga las categorías con `joinedload`, evitando consultas repetidas N+1.
7. Se verificó la compilación Python y el build de producción del frontend.

## Sobre los ROLLBACK del log

Los `ROLLBACK` mostrados después de endpoints GET con respuesta `200 OK` no representan un error. SQLAlchemy cierra la transacción de lectura sin guardar cambios.
