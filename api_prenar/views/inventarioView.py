from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.serializers.inventarioSerializers import InventarioSerializer

class InventarioView(APIView):
    def post(self, request):
        serializer=InventarioSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(
                    {"message":"Inventario registrado exitosamente", "data": serializer.data},
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"message":"Error al registrar el inventario", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(
            {"message":"Error al registrar el inventario", "error": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )