from rest_framework.views import APIView
from api_prenar.models import Cliente
from rest_framework.response import Response
from rest_framework import status
from api_prenar.serializers.clienteSerializers import ClienteDetailSerializer

class ClienteEspecificoView(APIView):
    def get(self, request, cliente_id):
        try:
            cliente_especifico=Cliente.objects.get(id=cliente_id)
            serializer=ClienteDetailSerializer(cliente_especifico)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Cliente.DoesNotExist:
            return Response(
                {"message":"Cliente no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
