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
            start_date = request.query_params.get('start_date', None)
            end_date = request.query_params.get('end_date', None)
            name_cliente=request.query_params.get('name_cliente',None)
            
            # Filtrar los inventarios por el id_producto proporcionado y aplicar los filtros adicionales si los parámetros están presentes
            filters = Q(id_producto=id_producto)

            if order_code:
                filters &= Q(id_pedido__order_code__icontains=order_code)
            
            if name_cliente:
                filters &= Q(id_pedido__id_client__name__icontains=name_cliente)
            
            # Filtrar por rango de fechas si 'start_date' y 'end_date' están presentes
            if start_date and end_date:
                filters &= Q(inventory_date__gte=start_date, inventory_date__lte=end_date)
            elif start_date:
                filters &= Q(inventory_date__gte=start_date)
            elif end_date:
                filters &= Q(inventory_date__lte=end_date)

            # Filtrar los inventarios aplicando los filtros
            inventarios = Inventario.objects.filter(filters).order_by('-id')

            # Si no se encuentran inventarios, devolver una respuesta vacía con mensaje
            if not inventarios.exists():
                return Response(
                    {"message": "No se encontraron registros con estos datos de búsqueda."},
                    status=status.HTTP_200_OK
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