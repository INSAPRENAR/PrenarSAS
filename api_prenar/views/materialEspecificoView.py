from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Material
from api_prenar.serializers.materialSerializers import MaterialSerializer
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination

class MaterialDetailView(APIView):
    def get(self, request, categoria_id):
        try:
            # Filtrar los materiales según la categoría proporcionada, ordenados por '-id'
            materiales = Material.objects.filter(id_categoria=categoria_id).order_by('-id')

            # Inicializar el paginador
            paginator = PageNumberPagination()
            paginator.page_size = 20  # Define el número de materiales por página (ajusta según tus necesidades)
            paginated_materiales = paginator.paginate_queryset(materiales, request)

            # Serializar los materiales paginados
            serializer = MaterialSerializer(paginated_materiales, many=True)

            if not materiales.exists():
                # Si no hay materiales, devolver un mensaje indicando que no se encontraron datos
                return Response(
                    {"message": "No se encontraron materiales para la categoría especificada.", "data": []},
                    status=status.HTTP_200_OK
                )

            # Retornar la respuesta paginada
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al obtener los materiales.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )