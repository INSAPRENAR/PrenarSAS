from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from api_prenar.serializers.consumoMaterialSerializers import ConsumoMaterialSerializer
from api_prenar.models.categoria_material import CategoriaMaterial
from api_prenar.models import ConsumoMaterial, Producto
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination

class ConsumoMaterialView(APIView):
    
    def post(self, request):
        try:
            serializer=ConsumoMaterialSerializer(data=request.data)
            if serializer.is_valid():
                id_categoria=serializer.validated_data.get('id_categoria')
                data_base_quantity_used=serializer.validated_data.get('base_quantity_used')
                data_quantity_mortar_used=serializer.validated_data.get('quantity_mortar_used')
                quantity_produced=serializer.validated_data.get('quantity_produced')
                id_producto=serializer.validated_data.get('id_producto')

                categoria_material=get_object_or_404(CategoriaMaterial, id=id_categoria.id)
                producto = get_object_or_404(Producto, id=id_producto.id)


                # Cálculos adicionales para los campos
                unit_X_base_package = quantity_produced / data_base_quantity_used if data_base_quantity_used != 0 else 0
                base_variation = unit_X_base_package - producto.base_estimated_units
                kilos_X_base_unit = data_base_quantity_used / quantity_produced if quantity_produced != 0 else 0

                unit_X_package_mortar = quantity_produced / data_quantity_mortar_used if data_quantity_mortar_used != 0 else 0
                mortar_variation = unit_X_package_mortar - producto.estimated_units_mortar
                kilos_X_unit_mortar = data_quantity_mortar_used / quantity_produced if quantity_produced != 0 else 0

                total = data_base_quantity_used + data_quantity_mortar_used

                nuevo_consumo_material=ConsumoMaterial.objects.create(
                    consumption_date=serializer.validated_data.get('consumption_date'),
                    id_categoria=categoria_material,
                    id_producto=producto,
                    quantity_produced=serializer.validated_data.get('quantity_produced'),
                    base_quantity_used=data_base_quantity_used,
                    quantity_mortar_used=data_quantity_mortar_used,
                    total=total,
                    email_user=serializer.validated_data.get('email_user'),
                    unit_X_base_package=unit_X_base_package,
                    estimated_base_reference_units=producto.base_estimated_units,
                    base_variation=base_variation,
                    kilos_X_base_unit=kilos_X_base_unit,
                    unit_X_package_mortar=unit_X_package_mortar,
                    estimated_units_reference_mortar=producto.estimated_units_mortar,
                    mortar_variation=mortar_variation,
                    kilos_X_unit_mortar=kilos_X_unit_mortar

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
            # Filtrar los consumos de materiales según la categoría proporcionada, ordenados por '-id'
            consumos = ConsumoMaterial.objects.filter(id_categoria=categoria_id).order_by('-id')

            # Inicializar el paginador
            paginator = PageNumberPagination()
            paginator.page_size = 20  # Define el número de consumos por página (ajusta según tus necesidades)
            paginated_consumos = paginator.paginate_queryset(consumos, request)

            if not consumos.exists():
                # Si no hay consumos, devolver un mensaje indicando que no se encontraron datos
                return Response(
                    {
                        "message": "No se encontraron consumos de materiales para la categoría especificada.",
                        "data": []
                    },
                    status=status.HTTP_200_OK
                )

            # Serializar los consumos paginados
            serializer = ConsumoMaterialSerializer(paginated_consumos, many=True)

            # Retornar la respuesta paginada con el mensaje
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {
                    "message": "Ocurrió un error al obtener los consumos de materiales.",
                    "error": str(e)
                },
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
