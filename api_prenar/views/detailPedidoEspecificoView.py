from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido
from api_prenar.serializers.detailPedidoSerializers import DetailPedidoEspecificoSerializer

class PedidoDetailEspecificoView(APIView):

    def get(self, request, pedido_id):
        try:
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            return Response(
                {"message": "Pedido no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Usamos el serializer para serializar solo los datos del pedido
        serializer = DetailPedidoEspecificoSerializer(pedido)
        return Response(
            {"message": "Pedido obtenido exitosamente", "Pedido": serializer.data},
            status=status.HTTP_200_OK
        )