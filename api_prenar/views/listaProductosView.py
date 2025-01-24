from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Producto
from api_prenar.serializers.productoSerializers import ProductoSerializer

class ListaProductoView(APIView):
    
    def get(self, request):
        productos = Producto.objects.all()
        if productos.exists():
            serializer = ProductoSerializer(productos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response([], status=status.HTTP_200_OK)  # Devolver array vacío
        
    