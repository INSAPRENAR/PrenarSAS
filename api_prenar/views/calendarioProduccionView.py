from rest_framework.views import APIView
from api_prenar.serializers.calendarioSerializers import CalendarioSerializer, CalendarioTipo1Serializer, CalendarioTipo2Serializer
from rest_framework.response import Response
from rest_framework import status, pagination
from api_prenar.models import Calendario
from django.db.models import Q

class CalendarioProduccionView(APIView):

    def post(self, request):
        try:
            serializer = CalendarioSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save() 
                return Response(
                    {"message": "Calendario registrado exitosamente.", "data": serializer.data},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {"message": "Error en los datos enviados.", "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al registrar el calendario.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request, tipo=None):
        try:
            # Obtener parámetros de filtro desde la URL
            start_date = request.query_params.get('start_date', None)
            end_date = request.query_params.get('end_date', None)
            order_code = request.query_params.get('order_code', None)
            product_name = request.query_params.get('product_name', None)
            # Filtrar los calendarios según el tipo
            if tipo == 1:
                calendarios = Calendario.objects.filter(type=1)
                serializer_class = CalendarioTipo1Serializer
            elif tipo == 2:
                calendarios = Calendario.objects.filter(type=2)
                serializer_class = CalendarioTipo2Serializer
            else:
                return Response(
                    {"data": [], "message": "Tipo no válido."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Construir el filtro adicional utilizando objetos Q
            filters = Q()
            # Filtro por rango de fecha en calendar_date
            if start_date and end_date:
                filters &= Q(calendar_date__gte=start_date, calendar_date__lte=end_date)
            elif start_date:
                filters &= Q(calendar_date__gte=start_date)
            elif end_date:
                filters &= Q(calendar_date__lte=end_date)

            # Filtro por order_code en el modelo Pedido (relacionado mediante id_pedido)
            if order_code:
                filters &= Q(id_pedido__order_code__icontains=order_code)

            # Filtro por name en el modelo Producto (relacionado mediante id_producto)
            if product_name:
                filters &= Q(id_producto__name__icontains=product_name)
            
            # Aplicar los filtros adicionales al queryset
            calendarios = calendarios.filter(filters)

            # Ordenar los calendarios por '-id'
            calendarios = calendarios.order_by('-id')

            # Verificar si hay calendarios para el tipo dado
            if not calendarios.exists():
                return Response(
                    {"data": [], "message": "No se encontraron calendarios para este tipo."},
                    status=status.HTTP_200_OK
                )

            # Configurar la paginación
            paginator = pagination.PageNumberPagination()
            paginator.page_size = 20  # Define el número de calendarios por página
            paginated_calendarios = paginator.paginate_queryset(calendarios, request)

            # Serializar los calendarios paginados
            serializer = serializer_class(paginated_calendarios, many=True)

            # Preparar la respuesta paginada con la estructura deseada
            response_data = {
                "data": serializer.data,
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"data": [], "message": "Ocurrió un error al obtener los calendarios.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, calendario_id=None):
        if not calendario_id:
            return Response(
                {"message": "Debe proporcionar el ID del calendario a eliminar."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Buscar el calendario por ID
            calendario = Calendario.objects.get(id=calendario_id)
            
            # Eliminar el calendario
            calendario.delete()
            
            return Response(
                {"message": f"Calendario con ID {calendario_id} eliminado exitosamente."},
                status=status.HTTP_200_OK
            )
        except Calendario.DoesNotExist:
            return Response(
                {"message": f"No se encontró un calendario con ID {calendario_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al eliminar el calendario.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )