from rest_framework.views import APIView
from api_prenar.serializers.calendarioSerializers import CalendarioSerializer, CalendarioListSerializer, CalendarioTipo1Serializer, CalendarioTipo2Serializer
from rest_framework.response import Response
from rest_framework import status, pagination
from api_prenar.models import Calendario
from django.db.models import Q
from datetime import datetime
from rest_framework.pagination import PageNumberPagination

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

    def put(self, request, calendario_id):
        try:
            try:
                instance = Calendario.objects.get(id=calendario_id)
            except Calendario.DoesNotExist:
                return Response(
                    {"message": f"No se encontró el calendario con ID {calendario_id}."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # partial=True: permite actualizar solo algunos campos
            serializer = CalendarioSerializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                updated = serializer.save()
                return Response(
                    {
                        "message": "Calendario actualizado exitosamente.",
                        "data": CalendarioSerializer(updated).data
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"message": "Error en los datos enviados.", "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al actualizar el calendario.", "error": str(e)},
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
    
    def get(self, request):
        try:
            start_from = request.query_params.get('start_date_from')
            start_to = request.query_params.get('start_date_to')

            qs = Calendario.objects.all()

            # Parse helper
            def parse_date(s):
                return datetime.strptime(s, '%Y-%m-%d').date()

            # Filtro SOLO por start_date (rango opcional)
            if start_from and start_to:
                d_from = parse_date(start_from)
                d_to = parse_date(start_to)
                qs = qs.filter(start_date__range=(d_from, d_to))
            elif start_from:
                d_from = parse_date(start_from)
                qs = qs.filter(start_date__gte=d_from)
            elif start_to:
                d_to = parse_date(start_to)
                qs = qs.filter(start_date__lte=d_to)

            # Orden fijo por id descendente
            qs = qs.order_by('-id')

            if not qs.exists():
                return Response([], status=status.HTTP_200_OK)

            # Paginación
            paginator = PageNumberPagination()
            paginator.page_size = 20  # ajusta si quieres
            page = paginator.paginate_queryset(qs, request)

            serializer = CalendarioListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except ValueError as e:
            # errores de parseo de fecha
            return Response(
                {
                    "message": "Parámetros de fecha inválidos. Usa formato YYYY-MM-DD.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"message": "Error al obtener los calendarios.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )