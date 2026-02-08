from rest_framework.views import APIView
from api_prenar.models import Cliente
from api_prenar.serializers.clienteSerializers import ClienteSerializer
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q

class ClientesCompletadosView(APIView):
    def get(self, request):
        #atributos para filtros
        name=request.query_params.get('name',None)
        identification=request.query_params.get('identification', None)
        
        # incluimos el número de pedidos completados (state=2) por cada cliente
        clientes = Cliente.objects.annotate(
            pedidos_completados=Count('pedidos', filter=Q(pedidos__state=2)),
            total_pedidos=Count('pedidos')
        ).filter(
            pedidos_completados__gt=0   # clientes con al menos 1 state=2
        )

        # Aplicar el filtro por nombre (búsqueda parcial e insensible a mayúsculas/minúsculas)
        if name:
            clientes = clientes.filter(name__icontains=name)
        
        # Aplicar el filtro por identificación (búsqueda parcial e insensible a mayúsculas/minúsculas)
        if identification:
            clientes = clientes.filter(identification__icontains=identification)

        # Ordenar los resultados, por ejemplo, de forma descendente según 'id'
        clientes = clientes.order_by('-id')

        # Configurar el paginador
        paginator = PageNumberPagination()
        paginator.page_size = 20  # Número de clientes por página
        paginated_clientes = paginator.paginate_queryset(clientes, request)

        # Serializar los datos paginados
        serializer = ClienteSerializer(paginated_clientes, many=True)

        # Retornar la respuesta con los datos paginados
        return paginator.get_paginated_response(serializer.data)