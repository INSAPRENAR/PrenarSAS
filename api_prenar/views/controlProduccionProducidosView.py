from django.http import JsonResponse
from api_prenar.models import Pedido
from api_prenar.options.utils import get_total_almacen

def control_produccion_agrupado_completados(request):
    # Obtener filtros de la query string (si se envían)
    pedido_code_filter = request.GET.get("pedido_code", "").lower()
    nombre_producto_filter = request.GET.get("nombre_producto", "").lower()

    pedidos = Pedido.objects.all()
    productos_agrupados = {}

    # Agrupamos los productos a partir de los pedidos
    for pedido in pedidos:
        cliente = {
            "id": pedido.id_client.id,
            "nombre": pedido.id_client.name
        }
        for producto in pedido.products:
            referencia = producto["referencia"]
            name_producto = producto["name"]
            color_producto = producto["color"]
            control_producto = producto["control"]
            control = producto.get("control", True)
            cantidad_pendiente = producto["cantidad_unidades"]

            if control == True:
                if referencia not in productos_agrupados:
                    productos_agrupados[referencia] = {
                        "id_producto": f"{referencia}",
                        "nombre_producto": f"{name_producto} {color_producto}",
                        "control": control_producto,
                        "total_a_deber": 0,
                        "total_almacen": 0,
                        "cantidadAlmacen_menosCantidadAdeber": 0,
                        "pedidos": []
                    }

                productos_agrupados[referencia]["pedidos"].append({
                    "pedido_id": pedido.id,
                    "pedido_code": pedido.order_code,
                    "fecha_entrega": pedido.delivery_date,
                    "cliente": cliente,
                    "cantidad_pendiente": cantidad_pendiente
                })

                productos_agrupados[referencia]["total_a_deber"] += cantidad_pendiente

    # Calcular totales de almacén para cada producto
    for referencia, datos in productos_agrupados.items():
        total_almacen = get_total_almacen(referencia)
        datos["total_almacen"] = total_almacen
        datos["cantidadAlmacen_menosCantidadAdeber"] = total_almacen - datos["total_a_deber"]

    # Aplicar filtros:
    # 1. Filtrar por nombre del producto (campo "nombre_producto")
    # 2. Filtrar los pedidos internos por pedido_code
    filtered_productos = []
    for prod in productos_agrupados.values():
        # Filtrar por nombre del producto si se especifica
        if nombre_producto_filter and nombre_producto_filter not in prod["nombre_producto"].lower():
            continue

        # Filtrar los pedidos de este producto según el pedido_code, si se especifica
        if pedido_code_filter:
            filtered_pedidos = [
                p for p in prod["pedidos"] 
                if pedido_code_filter in p["pedido_code"].lower()
            ]
            # Si después de filtrar no quedan pedidos, descartamos este producto
            if not filtered_pedidos:
                continue
            # Actualizamos los pedidos y recalculamos totales en función de los pedidos filtrados
            prod["pedidos"] = filtered_pedidos
            prod["total_a_deber"] = sum(p["cantidad_pendiente"] for p in filtered_pedidos)
            prod["cantidadAlmacen_menosCantidadAdeber"] = prod["total_almacen"] - prod["total_a_deber"]

        filtered_productos.append(prod)

    return JsonResponse({
        "message": "Control de producción completados generado exitosamente.",
        "productos": filtered_productos
    })