from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from api_prenar.models import Pedido

class ProductosPedidoDespachoView(APIView):

    def get(self, request, pedido_id):
        """
        Obtiene los productos de un pedido, mostrando nombre y color.
        """
        try:
            # Obtener el pedido
            pedido = get_object_or_404(Pedido, id=pedido_id)

            # Procesar los productos del JSON para incluir nombre y color
            productos = pedido.products
            productos_con_nombre_color = [
                {
                    "id_producto": producto["referencia"],
                    "name": producto.get("name", "Nombre no disponible"),
                    "color": producto.get("color", "Color no disponible"),
                }
                for producto in productos
            ]

            return Response(
                {
                    "productos": productos_con_nombre_color,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"message": "Error al obtener los productos del pedido.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )