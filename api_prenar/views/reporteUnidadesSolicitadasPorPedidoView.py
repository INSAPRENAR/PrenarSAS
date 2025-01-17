from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido

class PedidoProductosUnidadesSolicitadasView(APIView):
    def get(self, request):
        try:
            # Filtrar pedidos con state=1 y traer el cliente relacionado
            pedidos_activos = Pedido.objects.filter(state=1).select_related('id_client')

            # Construir la respuesta
            pedidos_data = []
            for pedido in pedidos_activos:
                productos_data = []
                for producto in pedido.products:  # Iterar sobre el JSON 'products'
                    productos_data.append({
                        "name": producto.get("name"),
                        "color": producto.get("color"),
                        "cantidad_unidades": producto.get("cantidad_unidades"),
                        "cantidades_despachadas": producto.get("cantidades_despachadas")
                    })
                
                pedidos_data.append({
                    "order_code": pedido.order_code,
                    "id_cliente": pedido.id_client.id,
                    "cliente_name": pedido.id_client.name,  # Nombre del cliente
                    "productos": productos_data  # Detalles de los productos
                })

            return Response(
                {
                    "message": "Pedidos activos con productos y detalles de cliente obtenidos exitosamente.",
                    "pedidos": pedidos_data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "message": "Error al obtener los pedidos activos con productos y detalles de cliente.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )