from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from api_prenar.serializers.consumoMaterialSerializers import ConsumoMaterialSerializer
from api_prenar.models.categoria_material import CategoriaMaterial
from api_prenar.models import ConsumoMaterial
from django.shortcuts import get_object_or_404

class ConsumoMaterialView(APIView):
    def post(self, request):
        try:
            serializer=ConsumoMaterialSerializer(data=request.data)
            if serializer.is_valid():
                id_categoria=serializer.validated_data.get('id_categoria')
                data_base_quantity_used=serializer.validated_data.get('base_quantity_used')
                data_quantity_mortar_used=serializer.validated_data.get('quantity_mortar_used')

                categoria_material=get_object_or_404(CategoriaMaterial, id=id_categoria.id)

                total = data_base_quantity_used + data_quantity_mortar_used

                nuevo_consumo_material=ConsumoMaterial.objects.create(
                    consumption_date=serializer.validated_data.get('consumption_date'),
                    id_categoria=categoria_material,
                    id_producto=serializer.validated_data.get('id_producto'),
                    quantity_produced=serializer.validated_data.get('quantity_produced'),
                    base_quantity_used=data_base_quantity_used,
                    quantity_mortar_used=data_quantity_mortar_used,
                    total=total,
                    email_user=serializer.validated_data.get('email_user')

                )

                categoria_material.stock_quantity -=total
                categoria_material.save()
                return Response(
                    {"message": "Material registrado y stock actualizado.", "data": ConsumoMaterialSerializer(nuevo_consumo_material).data},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"message":"Ocurrió un error al registrar el material.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def get(self, request, categoria_id):
        try:
            # Filtrar los materiales según la categoría
            materiales = ConsumoMaterial.objects.filter(id_categoria=categoria_id)

            if not materiales.exists():
                # Si no hay materiales, devolver un mensaje indicando que no se encontraron datos
                return Response(
                    {"message": "No se encontraron consumos de materiales para la categoría especificada.", "data": []},
                    status=status.HTTP_200_OK
                )

            # Serializar los materiales encontrados
            serializer = ConsumoMaterialSerializer(materiales, many=True)

            return Response(
                {"message": "Consumo Materiales obtenidos exitosamente.", "data": serializer.data},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al obtener los consumos de materiales.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, id):
        try:
            # Buscar el consumo de material por ID
            consumo_material = get_object_or_404(ConsumoMaterial, id=id)
            
            # Obtener la categoría asociada al material
            categoria_material = consumo_material.id_categoria

            # Restar el total del consumo de material al stock_quantity de la categoría
            categoria_material.stock_quantity += consumo_material.total
            categoria_material.save()

            # Eliminar el consumo del material
            consumo_material.delete()

            return Response(
                {"message": "Consumo Material eliminado y stock actualizado correctamente."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al eliminar el consumo del material.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
