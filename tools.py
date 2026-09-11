from langchain_core.tools import tool

PEDIDOS_DB = {
    102: {
        "pedidos": 3,
        "total": 14500,
        "ultimo_pedido": {"pedido_id": "P-1029", "fecha": "2026-08-02", "monto": 5200, "estado": "entregado"},
    },
    105: {
        "pedidos": 1,
        "total": 3200,
        "ultimo_pedido": {"pedido_id": "P-1041", "fecha": "2026-08-15", "monto": 3200, "estado": "en_camino"},
    },
    110: {
        "pedidos": 5,
        "total": 27800,
        "ultimo_pedido": {"pedido_id": "P-1055", "fecha": "2026-09-01", "monto": 6100, "estado": "entregado"},
    },
}


@tool
def buscar_pedidos(cliente_id: int) -> dict:
    """Busca cuantos pedidos hizo un cliente y el total gastado. Usar cuando
    pregunten cuantos pedidos tuvo un cliente o cuanto gasto en total. Si el
    cliente_id no existe devuelve un error, avisar al usuario en vez de
    inventar numeros."""
    cliente = PEDIDOS_DB.get(cliente_id)
    if cliente is None:
        return {"error": f"no se encontro el cliente {cliente_id}"}
    return {"pedidos": cliente["pedidos"], "total": cliente["total"]}


@tool
def buscar_detalle_ultimo_pedido(cliente_id: int) -> dict:
    """Busca el detalle del ultimo pedido de un cliente: numero, fecha,
    monto y estado. Usar cuando pregunten especificamente por el ultimo
    pedido o por su estado."""
    cliente = PEDIDOS_DB.get(cliente_id)
    if cliente is None:
        return {"error": f"no se encontro el cliente {cliente_id}"}
    return cliente["ultimo_pedido"]
