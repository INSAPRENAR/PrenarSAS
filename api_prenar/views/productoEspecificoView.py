from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Producto
from api_prenar.serializers.productoSerializers import ProductoSerializer

class ProductoEspecificoView(APIView):
    def get(self, request, producto_id):
        try:
            producto_especifico=Producto.objects.get(id=producto_id)
            serializer=ProductoSerializer(producto_especifico)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Producto.DoesNotExist:
            return Response(
                {
                    "message":"producto no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )