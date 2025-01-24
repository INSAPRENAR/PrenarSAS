from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Inventario
from api_prenar.serializers.inventarioSerializers import InventarioSerializerInventario
from rest_framework.pagination import PageNumberPagination

class InventarioPorProductoView(APIView):

    def get(self, request, id_producto):
        try:
            # Filtrar los inventarios por el id_producto proporcionado, ordenados por '-id'
            inventarios = Inventario.objects.filter(id_producto=id_producto).order_by('-id')

            if not inventarios.exists():
                return Response(
                    {"message": f"No se encontraron inventarios para el producto con ID {id_producto}."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Inicializar el paginador
            paginator = PageNumberPagination()
            paginator.page_size = 20  # Define el número de inventarios por página (ajusta según tus necesidades)
            paginated_inventarios = paginator.paginate_queryset(inventarios, request)

            # Serializar los inventarios paginados
            serializer = InventarioSerializerInventario(paginated_inventarios, many=True)

            # Retornar la respuesta paginada
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {"message": "Error al obtener los inventarios por producto.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )