from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.serializers.pedidoSerializers import PedidoSerializer, PedidoDetailSerializer
from api_prenar.models import Cliente, Pedido, Inventario, Calendario, Despacho, Pago
from django.db import transaction
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.db.models import Sum

class PedidoView(APIView):

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
        filters = Q(id_client=cliente)
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
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            return Response(
                {"message": "Pedido no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Serializa el pedido con los nuevos datos
        serializer = PedidoDetailSerializer(pedido, data=request.data)
        
        if serializer.is_valid():
            # Guarda los cambios en el pedido
            updated_pedido = serializer.save()

            # Aquí es importante actualizar el campo `outstanding_balance` directamente
            total_calculado = 0.0
            total_pagado = Pago.objects.filter(id_pedido=pedido.id).aggregate(Sum('amount'))['amount__sum'] or 0.0
            
            # Calculamos el nuevo saldo pendiente
            total_calculado = updated_pedido.total - total_pagado
            updated_pedido.outstanding_balance = total_calculado
            updated_pedido.save()  # Guardamos el pedido con el nuevo saldo pendiente

            return Response(
                {"message": "Pedido actualizado exitosamente", "Pedido": serializer.data},
                status=status.HTTP_200_OK
            )

        # Si hay un error de validación, retornamos los errores
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

                # Verificar si existen pagos asociados a este pedido
                existe_pagos = Pago.objects.filter(id_pedido=pedido).exists()
                
                # Si existen despachos, inventarios o calendarios asociados, no permitir la eliminación
                if existe_despacho or existe_inventario or existe_calendario or existe_pagos:
                    mensajes = []
                    if existe_despacho:
                        mensajes.append("tiene despachos asociados.")
                    if existe_inventario:
                        mensajes.append("tiene registros en inventarios asociados.")
                    if existe_calendario:
                        mensajes.append("tiene registros en calendarios asociados.")
                    if existe_pagos:
                        mensajes.append("tiene registros en pagos asociados.")
                    
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
                    status=status.HTTP_200_OK
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
