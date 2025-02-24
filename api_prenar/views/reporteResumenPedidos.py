from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido
from api_prenar.serializers.reportePedidosResumenSerializers import ReportePedidosResumenSerializer
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination

class reportePedidosResumenView(APIView):
    def get(self, request):
        try:
            # Obtener los parámetros de búsqueda desde la URL
            order_code = request.query_params.get('order_code', None)
            start_date = request.query_params.get('start_date', None)
            end_date = request.query_params.get('end_date', None)
            name_cliente = request.query_params.get('name_cliente', None)

            # Construcción dinámica de los filtros
            filters = Q()

            if order_code:
                filters &= Q(order_code__icontains=order_code)

            if name_cliente:
                filters &= Q(id_client__name__icontains=name_cliente)

            if start_date and end_date:
                filters &= Q(order_date__gte=start_date, order_date__lte=end_date)
            elif start_date:
                filters &= Q(order_date__gte=start_date)
            elif end_date:
                filters &= Q(order_date__lte=end_date)

            # Filtrar los pedidos aplicando los filtros construidos
            pedidos = Pedido.objects.filter(filters).order_by('-order_date')

            # Si no hay registros, retornar mensaje vacío
            if not pedidos.exists():
                return Response(
                    {"message": "No se encontraron pedidos con los filtros especificados."},
                    status=status.HTTP_200_OK
                )

            # Inicializar y configurar el paginador
            paginator = PageNumberPagination()
            paginator.page_size = 20  # Ajusta el tamaño de página según tus necesidades
            paginated_pedidos = paginator.paginate_queryset(pedidos, request)

            # Serializar los pedidos paginados
            serializer = ReportePedidosResumenSerializer(paginated_pedidos, many=True)

            # Retornar la respuesta paginada
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {"message": "Error al obtener los pedidos.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )