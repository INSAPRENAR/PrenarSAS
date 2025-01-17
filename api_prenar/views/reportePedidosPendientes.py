from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido

class PedidoCountView(APIView):
    def get(self, request):
        try:
            # Contar los pedidos con state=1
            pedidos_con_state_1 = Pedido.objects.filter(state=1).count()

            return Response(
                {
                    "message": "Cantidad total de pedidos con state=1 obtenida exitosamente.",
                    "total_pedidos_pendientes": pedidos_con_state_1
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {
                    "message": "Error al obtener la cantidad de pedidos con state=1.",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )