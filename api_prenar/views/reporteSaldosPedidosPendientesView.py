from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido

class PedidoSaldosPendientesView(APIView):
    def get(self, request):
        try:
            # Obtener pedidos con state=1
            pedidos = Pedido.objects.filter(outstanding_balance__gt=0).select_related('id_client')

            # Construir la respuesta con los datos requeridos
            pedidos_data = [
                {
                    "order_code": pedido.order_code,
                    "id_cliente": pedido.id_client.id,
                    "cliente_name": pedido.id_client.name,  # Nombre del cliente
                    "total": pedido.total,
                    "outstanding_balance": pedido.outstanding_balance,
                }
                for pedido in pedidos
            ]

            return Response(
                {
                    "message": "Lista de pedidos con state=1 e información del cliente obtenida exitosamente.",
                    "pedidos": pedidos_data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "message": "Error al obtener la lista de pedidos con state=1.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )