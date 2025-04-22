from rest_framework.views import APIView
from api_prenar.models import Inventario
from rest_framework.response import Response
from rest_framework import status
from api_prenar.serializers.inventarioSerializers import InventarioSerializerInventario, InventarioSerializerInventarioDos

class InventarioEspecificoUpdateView(APIView):
    def get(self, request, inventario_id):
        try:
            inventario = Inventario.objects.get(id=inventario_id)
        except Inventario.DoesNotExist:
            return Response(
                {"message": "Inventario no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Selección dinámica de serializador según inventory_type
        if inventario.inventory_type == 1:
            serializer_class = InventarioSerializerInventario
        elif inventario.inventory_type == 2:
            serializer_class = InventarioSerializerInventarioDos
        else:
            return Response(
                {"message": "Tipo de inventario inválido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = serializer_class(inventario)
        return Response(serializer.data, status=status.HTTP_200_OK)