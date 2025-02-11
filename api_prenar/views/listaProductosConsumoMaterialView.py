from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from api_prenar.models import ConsumoMaterial
from api_prenar.serializers.productoSerializers import ProductoSerializer

class ConsumoMaterialListView(APIView):
    def get(self, request, categoria_id):
        # Filtrar los consumos de material por id_categoria
        consumos = ConsumoMaterial.objects.filter(id_categoria=categoria_id).distinct('id_producto')

        # Verificar si existen consumos de material para la categoría
        if not consumos:
            return Response(
                {"message": "No hay productos registrados para este material en esta categoría."},
                status=status.HTTP_404_NOT_FOUND  # No encontrado
            )

        # Crear una lista de los productos relacionados con la categoría
        productos = []
        for consumo in consumos:
            # Obtener los detalles del producto
            producto = consumo.id_producto
            producto_data = ProductoSerializer(producto).data
            productos.append(producto_data)

        return Response(productos, status=status.HTTP_200_OK)