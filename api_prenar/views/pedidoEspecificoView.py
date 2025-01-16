from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido
from api_prenar.serializers.pedidoEspecificoSerializers import PedidoSerializer

class PedidoDetailView(APIView):
    def get(self, request, pedido_id):
        try:
            # Obtener el pedido por su ID
            pedido = Pedido.objects.get(id=pedido_id)
            # Serializar el pedido
            serializer = PedidoSerializer(pedido)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Pedido.DoesNotExist:
            return Response(
                {"message": "Pedido no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )