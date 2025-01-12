from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models.categoria_material import CategoriaMaterial
from api_prenar.serializers.categoriaMaterialSerializers import CategoriaMaterialSerializer

class CategoriaMaterialDetail(APIView):
    def get(self, request, categoria_id, format=None):
        try:
            categoria = CategoriaMaterial.objects.get(id=categoria_id)
            serializer = CategoriaMaterialSerializer(categoria)
            return Response(serializer.data)
        except CategoriaMaterial.DoesNotExist:
            return Response({'error': 'Categoría de material no encontrada'}, status=status.HTTP_404_NOT_FOUND)