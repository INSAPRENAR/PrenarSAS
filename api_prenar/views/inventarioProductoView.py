from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Inventario
from api_prenar.serializers.inventarioSerializers import InventarioSerializerInventario
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

class InventarioPorProductoView(APIView):

    def get(self, request, id_producto):
        try:
            # Obtener los parámetros de búsqueda
            order_code = request.query_params.get('order_code', None)
            year = request.query_params.get('year', None)
            month = request.query_params.get('month', None)
            
            # Filtrar los inventarios por el id_producto proporcionado
            # y aplicar los filtros adicionales si los parámetros están presentes
            filters = Q(id_producto=id_producto)
            
            if order_code:
                filters &= Q(id_pedido__order_code=order_code)
            
            if year and month:
                filters &= Q(inventory_date__year=year, inventory_date__month=month)

            # Filtrar los inventarios aplicando los filtros
            inventarios = Inventario.objects.filter(filters).order_by('-id')

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