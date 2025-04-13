from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido, Producto

class ProductosEnPedidosPendientesView(APIView):
    def get(self, request):
        try:
            # Filtrar pedidos con state=1
            pedidos_pendientes = Pedido.objects.filter(state=1)

            # Extraer referencias únicas de los productos
            # cuya `cantidad_unidades` sea != `cantidades_despachadas`
            referencias_productos = set()

            for pedido in pedidos_pendientes:
                for producto in pedido.products:
                    referencia = producto.get('referencia')
                    
                    if referencia is None:
                        continue  # Si no hay 'referencia', ignorar

                    cantidad_unidades = producto.get('cantidad_unidades', 0)
                    cantidades_despachadas = producto.get('cantidades_despachadas', 0)

                    # Solo si la cantidad solicitada es diferente a la despachada
                    if cantidad_unidades != cantidades_despachadas:
                        referencias_productos.add(referencia)

            # Obtener los productos del modelo `Producto` basados en dichas referencias
            productos = Producto.objects.filter(id__in=referencias_productos)

            # Crear la respuesta con la info requerida
            productos_data = [
                {
                    "id": producto.id,
                    "name": producto.name,
                    "cantidad_conforme": producto.warehouse_quantity_conforme,
                    "cantidad_not_conforme": producto.warehouse_quantity_not_conforme,
                    "codigo": producto.product_code,
                    "color": producto.color
                }
                for producto in productos
            ]

            return Response(
                {
                    "message": "Productos pendientes (cantidad_unidades != cantidades_despachadas) obtenidos exitosamente.",
                    "productos": productos_data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "message": "Error al obtener los productos en pedidos pendientes.",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )