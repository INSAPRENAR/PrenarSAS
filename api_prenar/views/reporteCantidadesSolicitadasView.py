from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido, Producto

class CantidadesTotalesProductosPendientesView(APIView):
    def get(self, request):
        try:
            # Filtrar pedidos pendientes (state=1)
            pedidos_pendientes = Pedido.objects.filter(state=1)

            # Diccionario para acumular las cantidades faltantes por referencia
            cantidades_faltantes = {}

            for pedido in pedidos_pendientes:
                for producto in pedido.products:
                    referencia = producto.get("referencia")
                    cantidad_unidades = producto.get("cantidad_unidades", 0)
                    cantidades_despachadas = producto.get("cantidades_despachadas", 0)
                    
                    # Calcular lo que falta despachar de este producto
                    diferencia = cantidad_unidades - cantidades_despachadas

                    # Solo interesan los productos con faltante (diferencia > 0)
                    if referencia is not None and diferencia > 0:
                        if referencia not in cantidades_faltantes:
                            cantidades_faltantes[referencia] = 0
                        cantidades_faltantes[referencia] += diferencia

            # Obtener los productos del modelo Producto que correspondan a las referencias con faltante
            productos = Producto.objects.filter(id__in=cantidades_faltantes.keys())

            # Crear la respuesta con nombre y la cantidad faltante total
            productos_data = [
                {
                    "name": producto.name,
                    "codigo": producto.product_code,
                    "color": producto.color,
                    "total_quantity_requested": cantidades_faltantes.get(producto.id, 0)
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