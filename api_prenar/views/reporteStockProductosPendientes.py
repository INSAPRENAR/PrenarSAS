from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido, Producto

class ProductosEnPedidosPendientesView(APIView):
    def get(self, request):
        try:
            # Filtrar pedidos con state=1
            pedidos_pendientes = Pedido.objects.filter(state=1)

            # Extraer referencias únicas de los productos en los pedidos pendientes
            referencias_productos = set()
            for pedido in pedidos_pendientes:
                for producto in pedido.products:
                    if 'referencia' in producto:
                        referencias_productos.add(producto['referencia'])

            # Obtener los productos correspondientes (usando `id` en lugar de `product_code`)
            productos = Producto.objects.filter(id__in=referencias_productos)

            # Construir la respuesta con la información requerida
            productos_data = [
                {
                    "id": producto.id,
                    "name": producto.name,
                    "cantidad": producto.warehouse_quantity
                }
                for producto in productos
            ]

            return Response(
                {
                    "message": "Productos en pedidos pendientes obtenidos exitosamente.",
                    "productos": productos_data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "message": "Error al obtener los productos en pedidos pendientes.",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )