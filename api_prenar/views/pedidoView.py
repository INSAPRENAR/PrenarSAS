from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.serializers.pedidoSerializers import PedidoSerializer
from api_prenar.models import Cliente, Pedido

class PedidoView(APIView):

    def get(self, request, cliente_id):
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response(
                {"message": "Cliente no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        # filter para obtener todos los pedidos
        pedidos = Pedido.objects.filter(id_client=cliente)
        if pedidos.exists():
            serializer = PedidoSerializer(pedidos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "El cliente no tiene pedidos registrados."},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        serializer = PedidoSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Verificar que el cliente exista
                cliente = Cliente.objects.get(id=serializer.validated_data['id_client'].id)
            except Cliente.DoesNotExist:
                return Response(
                    {"message": "Cliente no encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer.save()
            return Response(
                {"message": "Pedido creado exitosamente."},
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {"message": "Error al crear el pedido.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def put(self, request, pedido_id):

        try:
            pedido=Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            Response(
                {"message":"Pedido no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer=PedidoSerializer(pedido, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message":"Pedido actualizado exitosamente", "Pedido":serializer.data},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"message": "Error al actualizar el pedido.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request, pedido_id):
        try:
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            return Response(
                {"message": "Pedido no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        Pedido.delete()
        return Response(
            {"message": "Pedido eliminado exitosamente."},
            status=status.HTTP_204_NO_CONTENT
        )
