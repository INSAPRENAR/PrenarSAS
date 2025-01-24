from rest_framework.views import APIView
from api_prenar.serializers.calendarioSerializers import CalendarioSerializer, CalendarioTipo1Serializer, CalendarioTipo2Serializer
from rest_framework.response import Response
from rest_framework import status, pagination
from api_prenar.models import Calendario

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
            # Filtrar los calendarios según el tipo
            if tipo == 1:
                calendarios = Calendario.objects.filter(type=1).order_by('-id')
                serializer_class = CalendarioTipo1Serializer
            elif tipo == 2:
                calendarios = Calendario.objects.filter(type=2).order_by('-id')
                serializer_class = CalendarioTipo2Serializer
            else:
                return Response(
                    {"data": [], "message": "Tipo no válido."},
                    status=status.HTTP_400_BAD_REQUEST
                )

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