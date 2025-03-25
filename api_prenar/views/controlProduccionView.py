from django.http import JsonResponse
from api_prenar.models import Pedido
from api_prenar.options.utils import get_total_almacen

def control_produccion_agrupado(request):
    pedidos = Pedido.objects.all()
    productos_agrupados = {}

    for pedido in pedidos:
        cliente = {
            "id": pedido.id_client.id,
            "nombre": pedido.id_client.name
        }
        for producto in pedido.products:
            referencia = producto["referencia"]
            name_producto = producto["name"]
            color_producto = producto["color"]
            control = producto.get("control", False)
            cantidad_pendiente = producto["cantidad_unidades"]

            if control == False:
                if referencia not in productos_agrupados:
                    productos_agrupados[referencia] = {
                        "id_producto": f"{referencia}",
                        "nombre_producto": f"{name_producto} {color_producto}",
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

    for referencia, datos in productos_agrupados.items():
        total_almacen = get_total_almacen(referencia)
        datos["total_almacen"] = total_almacen
        datos["cantidadAlmacen_menosCantidadAdeber"] =  total_almacen - datos["total_a_deber"]

    return JsonResponse({
        "message": "Control de producción generado exitosamente.",
        "productos": list(productos_agrupados.values())
    })