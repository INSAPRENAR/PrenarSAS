from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from api_prenar.serializers.consumoMaterialSerializers import ConsumoMaterialSerializer
from api_prenar.models.categoria_material import CategoriaMaterial
from api_prenar.models import ConsumoMaterial, Producto
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

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
                estimated_base=serializer.validated_data.get('estimated_base_reference_units')
                estimated_mortar=serializer.validated_data.get('estimated_units_reference_mortar')
                unit_value = serializer.validated_data.get('unit')

                categoria_material=get_object_or_404(CategoriaMaterial, id=id_categoria.id)
                producto = get_object_or_404(Producto, id=id_producto.id)


                # Cálculos adicionales para los campos
                unit_X_base_package = quantity_produced / data_base_quantity_used if data_base_quantity_used != 0 else 0
                base_variation = unit_X_base_package - estimated_base
                kilos_X_base_unit = data_base_quantity_used / quantity_produced if quantity_produced != 0 else 0

                unit_X_package_mortar = quantity_produced / data_quantity_mortar_used if data_quantity_mortar_used != 0 else 0
                mortar_variation = unit_X_package_mortar - estimated_mortar
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
                    estimated_base_reference_units=estimated_base,
                    base_variation=base_variation,
                    kilos_X_base_unit=kilos_X_base_unit,
                    unit_X_package_mortar=unit_X_package_mortar,
                    estimated_units_reference_mortar=estimated_mortar,
                    mortar_variation=mortar_variation,
                    kilos_X_unit_mortar=kilos_X_unit_mortar,
                    unit=unit_value

                )

                if unit_value == 1:
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


    def get(self, request, categoria_id, producto_id):
        try:
            # Obtener parámetros de fecha para filtrar consumption_date
            start_date = request.query_params.get('start_date', None)
            end_date = request.query_params.get('end_date', None)

            # Construir el filtro inicial: consumos para la categoría y producto dados
            filters = Q(id_categoria=categoria_id) & Q(id_producto=producto_id)

            # Agregar el filtro para consumption_date según las fechas recibidas
            if start_date and end_date:
                filters &= Q(consumption_date__gte=start_date, consumption_date__lte=end_date)
            elif start_date:
                filters &= Q(consumption_date__gte=start_date)
            elif end_date:
                filters &= Q(consumption_date__lte=end_date)

            # Aplicar los filtros y ordenar los consumos por '-id'
            consumos = ConsumoMaterial.objects.filter(filters).select_related('id_categoria', 'id_producto').order_by('-id')

            # Inicializar el paginador
            paginator = PageNumberPagination()
            paginator.page_size = 20  # Número de consumos por página
            paginated_consumos = paginator.paginate_queryset(consumos, request)

            if not consumos.exists():
                return Response(
                    {
                        "message": "No se encontraron consumos de materiales para la categoría y producto especificados.",
                        "data": []
                    },
                    status=status.HTTP_200_OK
                )

            # Serializar los consumos paginados
            serializer = ConsumoMaterialSerializer(paginated_consumos, many=True)

            # Retornar la respuesta paginada
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

            # Verificar si el campo unit es 1 para actualizar el stock
            if consumo_material.unit == 1:
                # Sumar el total del consumo de material al stock_quantity de la categoría
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
