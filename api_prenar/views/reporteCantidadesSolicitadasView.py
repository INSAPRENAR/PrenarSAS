from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido, Producto

class CantidadesTotalesProductosPendientesView(APIView):
    def get(self, request):
        try:
            # Filtrar pedidos pendientes (state=1)
            pedidos_pendientes = Pedido.objects.filter(state=1)

            # Diccionario para acumular la suma de cantidad_unidades por referencia
            cantidades_totales = {}

            for pedido in pedidos_pendientes:
                for producto in pedido.products:
                    referencia = producto.get("referencia")
                    cantidad_unidades = producto.get("cantidad_unidades", 0)
                    control = producto.get("control", False)  # Obtener el valor de 'control', por defecto 0
                    
                    # Solo considerar productos con 'control' > 0
                    if referencia is not None and control == False:
                            if referencia not in cantidades_totales:
                                cantidades_totales[referencia] = 0
                            cantidades_totales[referencia] += cantidad_unidades

            # Obtener los productos del modelo Producto que correspondan a las referencias con faltante
            productos = Producto.objects.filter(id__in=cantidades_totales.keys())

            # Crear la respuesta con nombre y la cantidad faltante total
            productos_data = [
                {
                    "name": producto.name,
                    "codigo": producto.product_code,
                    "color": producto.color,
                    "total_quantity_requested": cantidades_totales.get(producto.id, 0)
                }
                for producto in productos
            ]

            return Response(
                {
                    "message": "Cantidades totales (faltantes) de productos en pedidos pendientes obtenidas exitosamente.",
                    "productos": productos_data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "message": "Error al obtener las cantidades totales de productos en pedidos pendientes.",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )