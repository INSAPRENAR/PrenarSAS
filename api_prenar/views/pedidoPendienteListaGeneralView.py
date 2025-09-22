from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido
from api_prenar.serializers.pedidoPendienteListaGeneralSerializers import PedidoPendientesListaGeneralSerializer
from rest_framework.pagination import PageNumberPagination

class PedidoPendienteListaGeneralView(APIView):
    def get(self, request):
        # Filtros opcionales
        order_code = request.query_params.get('order_code', None)
        client_name = request.query_params.get('client_name', None)

        # Base: solo pedidos con state = 1
        pedidos = (Pedido.objects
                   .select_related('id_client'))

        # Aplicar filtros
        if order_code:
            pedidos = pedidos.filter(order_code__icontains=order_code)

        if client_name:
            # búsqueda por nombre de cliente (insensible a mayúsculas)
            pedidos = pedidos.filter(id_client__name__icontains=client_name)


        # Orden (más recientes primero)
        pedidos = pedidos.order_by('-id')

        # Paginación (20 por página)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(pedidos, request)

        # Serializar y responder paginado
        serializer = PedidoPendientesListaGeneralSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)