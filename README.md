# Practica-2

Proyecto de práctica para la asignatura Fundamentos de Back-end con Python. API para gestionar productos y pedidos utilizando estructuras de datos avanzadas, serializacion y deserealizacion con JSON, .

**Ejecutar**

Instala dependencias (si las agregas en `requirements.txt`) y ejecuta con `uvicorn`:

```bash
pip install -r requirements.txt
uvicorn main:app --reload 
```

**Archivos de persistencia**

- `productos.json` — almacena la lista de productos (generada por el servicio).
- `pedidos.json` — almacena la lista de pedidos.

**Dependencias principales**

- `fastapi` — framework web.
- `pydantic` — validación y modelos.
- `uvicorn` — servidor ASGI para desarrollo.

**Estructura principal**

- `main.py` — contiene la aplicación FastAPI, modelos Pydantic, un árbol binario de búsqueda (BST) para productos y una lista enlazada para pedidos.

**Modelos y estructuras**

- `Producto` (Pydantic): campos `id: int`, `name: str`, `price: float`, `stock: int`.
- `ArbolProductosBST`: árbol binario de búsqueda por `id` que permite `insertar`, `inorder`, `buscar`, `guardar_json` y `cargar_json`.
	- `inorder()` devuelve la lista de productos ordenada por `id`.
	- Los productos se persisten en `productos.json` tras cambios.
- `Pedido`, `PedidoItem`, `PedidoResponse`, `PedidoItemResponse`: modelos para representar pedidos y respuestas enriquecidas con datos de producto.
- `ListaPedidos`: implementación simple de lista enlazada con operaciones CRUD (append, find, update, delete), serialización a `pedidos.json` y carga inicial.

**Comportamiento de persistencia**

- Al iniciar, el módulo carga `productos.json` y `pedidos.json` si existen.
- Al agregar o modificar recursos, los cambios se escriben de nuevo en los respectivos JSON.

**Endpoints disponibles**

- `POST /productos` — Agrega un producto o varios.
	- Body: objeto `Producto` o lista de `Producto`.
	- Validaciones: no permite `id` duplicados (ni en la petición ni contra los existentes).
	- Respuesta: mensaje y el/los producto(s) agregado(s).
	- Ejemplo (un producto):
		```json
		{
			"id": 1,
			"name": "Lapicera",
			"price": 1.5,
			"stock": 100
		}
		```

- `GET /productos` — Devuelve la lista ordenada de productos (inorder).

- `GET /productos/{product_id}` — Devuelve un producto por `id` o 404 si no existe.

- `POST /pedidos` — Crea un pedido.
	- Body: objeto `Pedido` con `items: [{"producto_id": int, "quantity": int}, ...]`.
	- Validaciones: cada `producto_id` debe existir y la cantidad debe ser menor o igual al `stock` disponible.
	- Respuesta: mensaje y el pedido creado (con `id` asignado si no se proporciona).
	- Ejemplo (pedido):
		```json
		{
			"items": [
				{"producto_id": 1, "quantity": 2},
				{"producto_id": 3, "quantity": 1}
			]
		}
		```

- `GET /pedidos` — Lista todos los pedidos enriquecidos (incluye `name`, `price` y `subtotal` por item y `total`).

- `GET /pedidos/{pedido_id}` — Obtiene un pedido enriquecido por `id`.

- `PUT /pedidos/{pedido_id}` — Actualiza un pedido existente (mismas validaciones que crear).

- `DELETE /pedidos/{pedido_id}` — Elimina un pedido por `id`.

**Notas de uso y desarrollo**

- Para pruebas rápidas puedes usar Postman.

Ejemplo: agregar un producto con Postman:

- URL: `POST http://127.0.0.1:8000/productos`
- Headers: `Content-Type: application/json`
- Body (raw JSON):

```json
{
	"id": 10,
	"name": "Taza",
	"price": 4.5,
	"stock": 20
}
```

Ejemplo: crear un pedido con Postman:

- URL: `POST http://127.0.0.1:8000/pedidos`
- Headers: `Content-Type: application/json`
- Body (raw JSON):

```json
{
	"items": [
		{"producto_id": 10, "quantity": 2}
	]
}
```

**Ejemplos de respuestas completas**

- `POST /productos` (éxito, un producto):

```json
{
	"mensaje": "Producto agregado",
	"producto": {
		"id": 10,
		"name": "Taza",
		"price": 4.5,
		"stock": 20
	}
}
```

- `POST /productos` (éxito, varios productos):

```json
{
	"mensaje": "Productos agregados",
	"productos": [
		{"id": 11, "name": "Vaso", "price": 3.0, "stock": 30},
		{"id": 12, "name": "Plato", "price": 5.0, "stock": 15}
	]
}
```

- `GET /productos` (éxito):

```json
[
	{"id": 10, "name": "Taza", "price": 4.5, "stock": 20},
	{"id": 11, "name": "Vaso", "price": 3.0, "stock": 30}
]
```

- `GET /productos/{product_id}` (éxito):

```json
{
	"id": 10,
	"name": "Taza",
	"price": 4.5,
	"stock": 20
}
```

- `POST /pedidos` (éxito):

```json
{
	"mensaje": "Pedido creado",
	"pedido": {
		"id": 1,
		"items": [
			{"producto_id": 10, "quantity": 2}
		]
	}
}
```

- `GET /pedidos` (éxito):

```json
[
	{
		"id": 1,
		"items": [
			{"producto_id": 10, "quantity": 2, "name": "Taza", "price": 4.5, "subtotal": 9.0}
		],
		"total": 9.0
	}
]
```

- `GET /pedidos/{pedido_id}` (éxito):

```json
{
	"id": 1,
	"items": [
		{"producto_id": 10, "quantity": 2, "name": "Taza", "price": 4.5, "subtotal": 9.0}
	],
	"total": 9.0
}
```

- `PUT /pedidos/{pedido_id}` (éxito):

```json
{
	"mensaje": "Pedido actualizado",
	"pedido": {
		"id": 1,
		"items": [
			{"producto_id": 10, "quantity": 3}
		]
	}
}
```

- `DELETE /pedidos/{pedido_id}` (éxito):

```json
{
	"mensaje": "Pedido eliminado"
}
```

**Ejemplos de errores comunes**

- Producto duplicado (al POST /productos):

```json
{ "detail": "Producto con id 10 ya existe" }
```

- Recurso no encontrado (GET /productos/{id} u otros):

```json
{ "detail": "Producto no encontrado" }
```


