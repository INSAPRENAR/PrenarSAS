from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Inventario
from api_prenar.serializers.inventarioSerializers import InventarioSerializerInventario

class InventarioPorProductoView(APIView):

    def get(self, request, id_producto):
        try:
            # Filtrar los inventarios por el id_producto proporcionado
            inventarios = Inventario.objects.filter(id_producto=id_producto).order_by('-id')

            if not inventarios.exists():
                return Response(
                    {"message": f"No se encontraron inventarios para el producto con ID {id_producto}."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Serializar los inventarios encontrados
            serializer = InventarioSerializerInventario(inventarios, many=True)

            return Response(
                {"message": "Inventarios obtenidos exitosamente.", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"message": "Error al obtener los inventarios por producto.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )