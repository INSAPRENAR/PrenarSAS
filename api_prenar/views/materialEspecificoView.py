from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Material
from api_prenar.serializers.materialSerializers import MaterialSerializer
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

class MaterialDetailView(APIView):
    def get(self, request, categoria_id):
        try:
            # Obtener los parámetros para filtrar por fecha
            start_date = request.query_params.get('start_date', None)
            end_date = request.query_params.get('end_date', None)

            # Construir el filtro inicial: materiales de la categoría
            filters = Q(id_categoria=categoria_id)

            # Agregar el filtro para el campo date_received según las fechas recibidas
            if start_date and end_date:
                filters &= Q(date_received__gte=start_date, date_received__lte=end_date)
            elif start_date:
                filters &= Q(date_received__gte=start_date)
            elif end_date:
                filters &= Q(date_received__lte=end_date)

            # Aplicar los filtros y ordenar los materiales por '-id'
            materiales = Material.objects.filter(filters).order_by('-id')

            # Si no se encuentran materiales, se retorna un mensaje con una lista vacía
            if not materiales.exists():
                return Response(
                    {"message": "No se encontraron materiales para la categoría especificada.", "data": []},
                    status=status.HTTP_200_OK
                )

            # Inicializar el paginador
            paginator = PageNumberPagination()
            paginator.page_size = 20  # Número de materiales por página
            paginated_materiales = paginator.paginate_queryset(materiales, request)

            # Serializar los materiales paginados
            serializer = MaterialSerializer(paginated_materiales, many=True)

            # Retornar la respuesta paginada
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al obtener los materiales.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )