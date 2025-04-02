from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Cliente, Pedido
from api_prenar.serializers.clienteSerializers import ClienteSerializer
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q

class ClientesView(APIView):
    def get(self, request):
        #atributos para filtros
        name=request.query_params.get('name',None)
        identification=request.query_params.get('identification', None)
        # incluimos el número de pedidos pendientes (state=1) por cada cliente
        clientes = Cliente.objects.annotate(
            pedidos_pendientes=Count('pedidos', filter=Q(pedidos__state=1))
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

    def post(self, request):
        serializer = ClienteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Guarda el cliente en la base de datos
            return Response(
                {"message": "Cliente creado exitosamente."},
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {"message": "Error al crear el cliente.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def put(self, request, cliente_id):
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response(
                {"message": "Cliente no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ClienteSerializer(cliente, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Cliente actualizado exitosamente.", "cliente": serializer.data},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"message": "Error al actualizar el cliente.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request, cliente_id):
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response(
                {"message": "Cliente no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar si hay pedidos relacionados con este cliente

        pedidos_existentes = Pedido.objects.filter(id_client=cliente).exists()
        if pedidos_existentes:
            return Response(
                {"message": "No se puede eliminar el cliente porque tiene pedidos creados."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Si no hay pedidos, se procede a eliminar el cliente
        cliente.delete()
        return Response(
            {"message": "Cliente eliminado exitosamente."},
            status=status.HTTP_200_OK
        )