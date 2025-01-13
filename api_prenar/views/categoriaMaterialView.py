from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models.categoria_material import CategoriaMaterial
from api_prenar.models.material import Material
from api_prenar.models.consumo_material import ConsumoMaterial
from api_prenar.serializers.materialSerializers import CategoriaMaterialSerializer
from django.shortcuts import get_object_or_404

class CategoriaMaterialView(APIView):
    def post(self, request):
        try:
            # Deserializar los datos del request
            serializer = CategoriaMaterialSerializer(data=request.data)
            if serializer.is_valid():
                # Guardar la categoría en la base de datos
                serializer.save()
                return Response(
                    {"message": "Categoría de material creada exitosamente.", "data": serializer.data},
                    status=status.HTTP_201_CREATED
                )
            else:
                # Si los datos no son válidos, devolver errores de validación
                return Response(
                    {"message": "Error en los datos enviados.", "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            # Manejo de cualquier otro error
            return Response(
                {"message": "Ocurrió un error al crear la categoría de material.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # DELETE con validación de relaciones
    def delete(self, request, categoria_id):
        try:
            # Buscar la categoría por ID
            categoria = get_object_or_404(CategoriaMaterial, id=categoria_id)
            
            # Verificar si existen materiales o consumos relacionados con la categoría
            existe_material = Material.objects.filter(id_categoria=categoria).exists()
            existe_consumo = ConsumoMaterial.objects.filter(id_categoria=categoria).exists()
            
            if existe_material or existe_consumo:
                return Response(
                    {"message": "No se puede eliminar la categoría porque tiene materiales o consumos asociados."},
                    status=status.HTTP_200_OK
                )
            
            # Si no hay relaciones, eliminar la categoría
            categoria.delete()
            
            return Response(
                {"message": "Categoría de material eliminada exitosamente."},
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al eliminar la categoria de material.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )