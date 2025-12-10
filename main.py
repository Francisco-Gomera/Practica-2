from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, ValidationError, TypeAdapter
from typing import Optional, List
import json
import os

app = FastAPI()

class Producto(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    
class NodoProducto:
    def __init__(self, producto: Producto):
        self.producto = producto
        self.izq: Optional["NodoProducto"] = None
        self.der: Optional["NodoProducto"] = None
        
class ArbolProductosBST:
    def __init__(self):
        self.raiz: Optional[NodoProducto] = None

    def insertar(self, producto: Producto):
        if self.raiz is None:
            self.raiz = NodoProducto(producto)
            return
        self._insertar_rec(self.raiz, producto)

    def _insertar_rec(self, nodo: NodoProducto, producto: Producto):
        if producto.id < nodo.producto.id:
            if nodo.izq is None:
                nodo.izq = NodoProducto(producto)
            else:
                self._insertar_rec(nodo.izq, producto)
        else:
            if nodo.der is None:
                nodo.der = NodoProducto(producto)
            else:
                self._insertar_rec(nodo.der, producto)

    def inorder(self):
        resultado = []
        self._inorder_rec(self.raiz, resultado)
        return resultado

    def _inorder_rec(self, nodo: Optional[NodoProducto], resultado: list):
        if nodo:
            self._inorder_rec(nodo.izq, resultado)
            resultado.append(nodo.producto.model_dump())
            self._inorder_rec(nodo.der, resultado)


    def guardar_json(self, filename: str):
        data = self.inorder()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def cargar_json(self, filename: str):
        if not os.path.exists(filename):
            return

        with open(filename, "r", encoding="utf-8") as f:
            productos = json.load(f)

        for p in productos:
            self.insertar(Producto(**p))

    def buscar(self, id: int) -> Optional[Producto]:
        nodo = self.raiz
        while nodo is not None:
            if id == nodo.producto.id:
                return nodo.producto
            elif id < nodo.producto.id:
                nodo = nodo.izq
            else:
                nodo = nodo.der
        return None
                
arbol_productos = ArbolProductosBST()

arbol_productos.cargar_json("productos.json")               
                
@app.post("/productos")
async def agregar_producto(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Body no es JSON válido")

    productos_a_agregar: List[Producto] = []
    
    try:
        if isinstance(data, list):
            adapter = TypeAdapter(List[Producto])
            productos_a_agregar = adapter.validate_python(data)
        elif isinstance(data, dict):
            productos_a_agregar = [Producto(**data)]
        else:
            raise HTTPException(status_code=400, detail="El body debe ser un objeto JSON o una lista de objetos")
    except ValidationError as e:
        
        raise HTTPException(status_code=400, detail=e.errors())
    
    ver_ids = set()
    for prod in productos_a_agregar:
        if arbol_productos.buscar(prod.id) is not None:
            raise HTTPException(status_code=400, detail=f"Producto con id {prod.id} ya existe")
        if prod.id in ver_ids:
            raise HTTPException(status_code=400, detail=f"Id duplicado en la petición: {prod.id}")
        ver_ids.add(prod.id)

    for prod in productos_a_agregar:
        arbol_productos.insertar(prod)

    arbol_productos.guardar_json("productos.json")

    if len(productos_a_agregar) == 1:
        return {"mensaje": "Producto agregado", "producto": productos_a_agregar[0].model_dump()}
    return {"mensaje": "Productos agregados", "productos": [p.model_dump() for p in productos_a_agregar]}

@app.get("/productos")
def listar_productos():
    return arbol_productos.inorder()


@app.get("/productos/{product_id}")
def obtener_producto(product_id: int):
    producto = arbol_productos.buscar(product_id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto.model_dump()

class PedidoItem(BaseModel):
    producto_id: int
    quantity: int


class PedidoItemResponse(BaseModel):
    producto_id: int
    quantity: int
    name: str
    price: float
    subtotal: float


class Pedido(BaseModel):
    id: Optional[int] = None
    items: List[PedidoItem]


class PedidoResponse(BaseModel):
    id: int
    items: List[PedidoItemResponse]
    total: float


class NodoPedido:
    def __init__(self, pedido: Pedido):
        self.pedido = pedido
        self.siguiente: Optional["NodoPedido"] = None


class ListaPedidos:
    def __init__(self):
        self.cabeza: Optional[NodoPedido] = None
        

    def _enrich_pedido(self, pedido: Pedido) -> PedidoResponse:
        items_enriquecidos = []
        total = 0.0
        for item in pedido.items:
            prod = arbol_productos.buscar(item.producto_id)
            if prod:
                subtotal = item.quantity * prod.price
                items_enriquecidos.append(
                    PedidoItemResponse(
                        producto_id=item.producto_id,
                        quantity=item.quantity,
                        name=prod.name,
                        price=prod.price,
                        subtotal=subtotal
                    )
                )
                total += subtotal
        return PedidoResponse(id=pedido.id, items=items_enriquecidos, total=total)

    def _next_id(self) -> int:
        max_id = 0
        nodo = self.cabeza
        while nodo:
            if nodo.pedido.id and nodo.pedido.id > max_id:
                max_id = nodo.pedido.id
            nodo = nodo.siguiente
        return max_id + 1

    def append(self, pedido: Pedido) -> Pedido:
        if pedido.id is None:
            pedido.id = self._next_id()
        nodo = NodoPedido(pedido)
        if not self.cabeza:
            self.cabeza = nodo
            return pedido
        cur = self.cabeza
        while cur.siguiente:
            cur = cur.siguiente
        cur.siguiente = nodo
        return pedido

    def find(self, id: int) -> Optional[Pedido]:
        nodo = self.cabeza
        while nodo:
            if nodo.pedido.id == id:
                return nodo.pedido
            nodo = nodo.siguiente
        return None

    def update(self, id: int, nuevo: Pedido) -> Optional[Pedido]:
        nodo = self.cabeza
        while nodo:
            if nodo.pedido.id == id:
                nuevo.id = id
                nodo.pedido = nuevo
                return nodo.pedido
            nodo = nodo.siguiente
        return None

    def delete(self, id: int) -> bool:
        prev = None
        nodo = self.cabeza
        while nodo:
            if nodo.pedido.id == id:
                if prev is None:
                    self.cabeza = nodo.siguiente
                else:
                    prev.siguiente = nodo.siguiente
                return True
            prev = nodo
            nodo = nodo.siguiente
        return False

    def to_list(self) -> List[dict]:
        resultado = []
        nodo = self.cabeza
        while nodo:
            resultado.append(nodo.pedido.model_dump())
            nodo = nodo.siguiente
        return resultado

    def to_list_enriquecido(self) -> List[dict]:
        resultado = []
        nodo = self.cabeza
        while nodo:
            pedido_enriquecido = self._enrich_pedido(nodo.pedido)
            resultado.append(pedido_enriquecido.model_dump())
            nodo = nodo.siguiente
        return resultado

    def guardar_json(self, filename: str):
        data = self.to_list()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def cargar_json(self, filename: str):
        if not os.path.exists(filename):
            return
        with open(filename, "r", encoding="utf-8") as f:
            try:
                pedidos = json.load(f)
            except Exception:
                return
        if not isinstance(pedidos, list):
            return
        for p in pedidos:
            if not isinstance(p, dict):
                continue
            items = [PedidoItem(**it) for it in p.get("items", [])]
            pedido = Pedido(id=p.get("id"), items=items)
            self.append(pedido)


lista_pedidos = ListaPedidos()
lista_pedidos.cargar_json("pedidos.json")

@app.post("/pedidos")
async def crear_pedido(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Body no es JSON válido")

    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Se espera un objeto JSON para crear un pedido")

    try:
        pedido_in = Pedido(**data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

    for it in pedido_in.items:
        producto = arbol_productos.buscar(it.producto_id)
        if producto is None:
            raise HTTPException(status_code=400, detail=f"Producto con id {it.producto_id} no existe")
        if it.quantity > producto.stock:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para producto {producto.name} (id: {it.producto_id}). Disponible: {producto.stock}, Solicitado: {it.quantity}")

    creado = lista_pedidos.append(pedido_in)
    lista_pedidos.guardar_json("pedidos.json")
    return {"mensaje": "Pedido creado", "pedido": creado.model_dump()}


@app.get("/pedidos")
def listar_pedidos():
    return lista_pedidos.to_list_enriquecido()


@app.get("/pedidos/{pedido_id}")
def obtener_pedido(pedido_id: int):
    pedido = lista_pedidos.find(pedido_id)
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    pedido_enriquecido = lista_pedidos._enrich_pedido(pedido)
    return pedido_enriquecido.model_dump()


@app.put("/pedidos/{pedido_id}")
async def actualizar_pedido(pedido_id: int, request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Body no es JSON válido")

    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Se espera un objeto JSON para actualizar el pedido")

    try:
        nuevo = Pedido(**data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

    for it in nuevo.items:
        producto = arbol_productos.buscar(it.producto_id)
        if producto is None:
            raise HTTPException(status_code=400, detail=f"Producto con id {it.producto_id} no existe")
        if it.quantity > producto.stock:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para producto {producto.name} (id: {it.producto_id}). Disponible: {producto.stock}, Solicitado: {it.quantity}")

    actualizado = lista_pedidos.update(pedido_id, nuevo)
    if actualizado is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    lista_pedidos.guardar_json("pedidos.json")
    return {"mensaje": "Pedido actualizado", "pedido": actualizado.model_dump()}


@app.delete("/pedidos/{pedido_id}")
def eliminar_pedido(pedido_id: int):
    ok = lista_pedidos.delete(pedido_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    lista_pedidos.guardar_json("pedidos.json")
    return {"mensaje": "Pedido eliminado"}