from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Cliente, Pedido
from api_prenar.serializers.clienteSerializers import ClienteSerializer

class ClientesView(APIView):
    def get(self, request):
        clientes = Cliente.objects.all()
        if clientes.exists():
            serializer = ClienteSerializer(clientes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "No se encontraron clientes."}, 
                status=status.HTTP_200_OK
            )

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
            status=status.HTTP_204_NO_CONTENT
        )