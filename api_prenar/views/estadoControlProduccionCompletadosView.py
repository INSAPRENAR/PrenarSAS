from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido

class UpdatePedidoProductControlCompletados(APIView):
    def put(self, request, pedido_id):
        id_producto = request.data.get('id_producto')
        if id_producto is None:
            return Response(
                {"message": "El campo 'id_producto' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            return Response(
                {"message": "Pedido no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        products = pedido.products
        found = False
        
        # Asegurarse de que id_producto sea un número
        id_producto = int(id_producto)
        
        for item in products:
            # Comparar la referencia como número
            if item.get('referencia') == id_producto:
                item['control'] = False
                found = True
                break
        
        if not found:
            return Response(
                {"message": f"No se encontró el producto con referencia {id_producto} en el pedido."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Guardar los cambios en el campo JSON y en el pedido
        pedido.products = products
        pedido.save()
        
        return Response(
            {"message": "Pedido actualizado exitosamente.", "products": pedido.products},
            status=status.HTTP_200_OK
        )