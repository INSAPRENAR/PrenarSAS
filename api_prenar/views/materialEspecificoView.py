from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Material
from api_prenar.serializers.materialSerializers import MaterialSerializer
from django.shortcuts import get_object_or_404

class MaterialDetailView(APIView):
    def get(self, request, categoria_id):
        try:
            # Filtrar los materiales según la categoría
            materiales = Material.objects.filter(id_categoria=categoria_id)

            if not materiales.exists():
                # Si no hay materiales, devolver un mensaje indicando que no se encontraron datos
                return Response(
                    {"message": "No se encontraron materiales para la categoría especificada.", "data": []},
                    status=status.HTTP_200_OK
                )

            # Serializar los materiales encontrados
            serializer = MaterialSerializer(materiales, many=True)

            return Response(
                {"message": "Materiales obtenidos exitosamente.", "data": serializer.data},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al obtener los materiales.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )