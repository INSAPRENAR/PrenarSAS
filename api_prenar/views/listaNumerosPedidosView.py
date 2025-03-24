from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido
from api_prenar.serializers.pedidoSerializers import ListaNumerosPedidoSerializer

class ListaNumerosPedidosView(APIView):
    def get(self, request):
        # Obtener todos los pedidos
        pedidos = Pedido.objects.all()

        # Serializar los pedidos con los campos id y order_code
        serializer = ListaNumerosPedidoSerializer(pedidos, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)