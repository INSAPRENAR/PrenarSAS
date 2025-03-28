from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Material
from api_prenar.models.categoria_material import CategoriaMaterial
from api_prenar.serializers.materialSerializers import MaterialSerializer, CategoriaMaterialSerializer
from django.shortcuts import get_object_or_404

class MaterialView(APIView):
    def post(self, request):
        try:
            # Deserializar los datos del request
            serializer = MaterialSerializer(data=request.data)
            if serializer.is_valid():
                # Extraer los datos necesarios del serializer
                categoria_id = serializer.validated_data.get('id_categoria')
                amount = serializer.validated_data.get('amount')
                unit_price = serializer.validated_data.get('unit_price')
                
                # Obtener la categoría asociada al material
                categoria_material = get_object_or_404(CategoriaMaterial, id=categoria_id.id)
                
                # Calcular el total del material
                total = unit_price

                # Crear el nuevo material
                nuevo_material = Material.objects.create(
                    id_categoria=categoria_material,
                    description=serializer.validated_data.get('description'),
                    supplier=serializer.validated_data.get('supplier'),
                    unit_price=unit_price,
                    date_received=serializer.validated_data.get('date_received'),
                    amount=amount,
                    extent=serializer.validated_data.get('extent'),
                    total=total,
                    email_user=serializer.validated_data.get('email_user')
                )

                # Actualizar el stock_quantity de la categoría
                categoria_material.stock_quantity += amount
                categoria_material.save()

                return Response(
                    {"message": "Material registrado y stock actualizado.", "data": MaterialSerializer(nuevo_material).data},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al registrar el material.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        try:
            # Obtener todas las categorías
            categorias = CategoriaMaterial.objects.all()

            # Serializar los datos
            serializer = CategoriaMaterialSerializer(categorias, many=True)

            return Response(
                {"message": "Categorías de material.", "data": serializer.data},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al obtener las categorías de material.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, id):
        try:
            # Buscar el material por ID
            material = get_object_or_404(Material, id=id)
            
            # Obtener la categoría asociada al material
            categoria_material = material.id_categoria

            # Restar el amount del material al stock_quantity de la categoría
            categoria_material.stock_quantity -= material.amount
            categoria_material.save()

            # Eliminar el material
            material.delete()

            return Response(
                {"message": "Material eliminado y stock actualizado correctamente."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al eliminar el material.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )