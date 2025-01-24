from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.serializers.pedidoSerializers import PedidoSerializer
from api_prenar.models import Cliente, Pedido, Inventario, Calendario, Despacho
from django.db import transaction
from rest_framework.pagination import PageNumberPagination

class PedidoView(APIView):

    def get(self, request, cliente_id):
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response(
                {"message": "Cliente no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Filtrar los pedidos asociados al cliente, ordenados por '-id'
        pedidos = Pedido.objects.filter(id_client=cliente).order_by('-id')

        if not pedidos.exists():
            return Response(
                {"message": "El cliente no tiene pedidos registrados."},
                status=status.HTTP_200_OK
            )

        # Inicializar el paginador
        paginator = PageNumberPagination()
        paginator.page_size = 20  # Define el número de pedidos por página
        paginated_pedidos = paginator.paginate_queryset(pedidos, request)

        # Serializar los pedidos paginados
        serializer = PedidoSerializer(paginated_pedidos, many=True)

        # Retornar la respuesta paginada
        return paginator.get_paginated_response(serializer.data)

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
            
            # Obtener los datos del cliente (address y phone)
            serializer.validated_data['address'] = cliente.address
            serializer.validated_data['phone'] = cliente.phone
            
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
            return Response(
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
            with transaction.atomic():
                # Buscar el pedido por su ID, utilizando select_related si es necesario
                pedido = Pedido.objects.select_related().get(id=pedido_id)
                
                # Verificar el estado del pedido
                if pedido.state == 2:
                    return Response(
                        {"message": "No se puede eliminar el pedido porque el estado del pedido es Completado."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Verificar si existen despachos asociados a este pedido
                existe_despacho = Despacho.objects.filter(id_pedido=pedido).exists()
                
                # Verificar si existen inventarios asociados a este pedido
                existe_inventario = Inventario.objects.filter(id_pedido=pedido).exists()
                
                # Verificar si existen calendarios asociados a este pedido
                existe_calendario = Calendario.objects.filter(id_pedido=pedido).exists()
                
                # Si existen despachos, inventarios o calendarios asociados, no permitir la eliminación
                if existe_despacho or existe_inventario or existe_calendario:
                    mensajes = []
                    if existe_despacho:
                        mensajes.append("tiene despachos asociados.")
                    if existe_inventario:
                        mensajes.append("tiene registros en inventarios asociados.")
                    if existe_calendario:
                        mensajes.append("tiene registros en calendarios asociados.")
                    
                    # Construir el mensaje de error concatenando las razones
                    mensaje_error = "No se puede eliminar el pedido porque " + " y ".join(mensajes)
                    
                    return Response(
                        {"message": mensaje_error},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Si no hay despachos, inventarios ni calendarios asociados, proceder a eliminar el pedido
                pedido.delete()
                
                return Response(
                    {"message": "Pedido eliminado exitosamente."},
                    status=status.HTTP_204_NO_CONTENT
                )
        
        except Pedido.DoesNotExist:
            return Response(
                {"message": f"Pedido con ID {pedido_id} no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": "Error al intentar eliminar el pedido.", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
