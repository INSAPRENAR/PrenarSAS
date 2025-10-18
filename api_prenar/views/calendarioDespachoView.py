from rest_framework.views import APIView
from api_prenar.serializers.calendarioDespachoSerializers import CalendarioListSerializer, CalendarioDespachoSerializer
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import CalendarioDespacho
from django.db.models import Q
from datetime import datetime
from rest_framework.pagination import PageNumberPagination

class CalendarioDespachoView(APIView):

    def get(self, request):
            try:
                start_from = request.query_params.get('start_date_from')
                start_to = request.query_params.get('start_date_to')

                qs = CalendarioDespacho.objects.all()

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
    
    def post(self, request):
        try:
            payload = request.data.copy()

            # Compatibilidad: si llega como 'production', remapear a 'dispatch'
            if 'dispatch' not in payload and 'production' in payload:
                payload['dispatch'] = payload.pop('production')

            serializer = CalendarioDespachoSerializer(data=payload)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "Calendario de despachos registrado exitosamente.", "data": serializer.data},
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {"message": "Error en los datos enviados.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al registrar el calendario de despachos.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, calendario_id):
        try:
            try:
                instance = CalendarioDespacho.objects.get(id=calendario_id)
            except CalendarioDespacho.DoesNotExist:
                return Response(
                    {"message": f"No se encontró el calendario de despachos con ID {calendario_id}."},
                    status=status.HTTP_404_NOT_FOUND
                )

            payload = request.data.copy()
            # Compatibilidad con 'production'
            if 'dispatch' not in payload and 'production' in payload:
                payload['dispatch'] = payload.pop('production')

            # partial=True permite actualizar solo algunos campos
            serializer = CalendarioDespachoSerializer(instance, data=payload, partial=True)
            if serializer.is_valid():
                updated = serializer.save()
                return Response(
                    {"message": "Calendario de despachos actualizado exitosamente.",
                     "data": CalendarioDespachoSerializer(updated).data},
                    status=status.HTTP_200_OK
                )
            return Response(
                {"message": "Error en los datos enviados.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al actualizar el calendario de despachos.", "error": str(e)},
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
            calendario = CalendarioDespacho.objects.get(id=calendario_id)
            
            # Eliminar el calendario
            calendario.delete()
            
            return Response(
                {"message": f"Calendario de despacho con ID {calendario_id} eliminado exitosamente."},
                status=status.HTTP_200_OK
            )
        except CalendarioDespacho.DoesNotExist:
            return Response(
                {"message": f"No se encontró un calendario con ID {calendario_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al eliminar el calendario de despacho.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )