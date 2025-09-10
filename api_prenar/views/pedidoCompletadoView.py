from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido, Cliente
from api_prenar.serializers.pedidoSerializers import PedidoSerializer
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

class PedidoCompletadosView(APIView):
    def get(self, request, cliente_id):
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response(
                {"message": "Cliente no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener los parámetros de búsqueda de la query string
        order_code = request.query_params.get('order_code', None)
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)

        # Crear filtros para los pedidos
        filters = Q(id_client=cliente)& Q(state=2)
        if order_code:
            filters &= Q(order_code__icontains=order_code)
        if start_date and end_date:
            filters &= Q(order_date__gte=start_date, order_date__lte=end_date)
        elif start_date:
            filters &= Q(order_date__gte=start_date)
        elif end_date:
            filters &= Q(order_date__lte=end_date)

        # Filtrar los pedidos según los criterios anteriores
        pedidos = Pedido.objects.filter(filters).order_by('-id')

        if not pedidos.exists():
            return Response(
                {"message": "El cliente no tiene pedidos registrados."},
                status=status.HTTP_200_OK
            )

        # Inicializar y configurar el paginador
        paginator = PageNumberPagination()
        paginator.page_size = 20
        paginated_pedidos = paginator.paginate_queryset(pedidos, request)

        # Serializar los pedidos paginados
        serializer = PedidoSerializer(paginated_pedidos, many=True)

        # Retornar la respuesta paginada
        return paginator.get_paginated_response(serializer.data)