from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido

class ProductosPedidoView(APIView):
    def get(self, request, pedido_id):
        try:
            # Buscar el pedido por su ID
            pedido = Pedido.objects.get(id=pedido_id)
            
            # Extraer la lista de productos
            productos = pedido.products
            
            # Filtrar solo los campos 'name', 'color' y 'referencia'
            productos_filtrados = [
                {
                    "name": producto.get("name"),
                    "color": producto.get("color"),
                    "referencia": producto.get("referencia")
                }
                for producto in productos
            ]
            
            return Response(productos_filtrados, status=status.HTTP_200_OK)
        
        except Pedido.DoesNotExist:
            return Response(
                {"message": "Pedido no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": f"Error al procesar la solicitud: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )