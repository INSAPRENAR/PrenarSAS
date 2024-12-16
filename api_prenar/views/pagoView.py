from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido, Pago
from api_prenar.serializers.pagoSerializers import PagoSerializer

class PagoView(APIView):
    def post(self, request):
        serializer = PagoSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Verificar si el pedido existe
                pedido = Pedido.objects.get(id=serializer.validated_data['id_pedido'].id)
            except Pedido.DoesNotExist:
                return Response(
                    {"message": "Pedido no encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Guardar el pago
            serializer.save()
            return Response(
                {"message": "Pago registrado exitosamente.", "Pago": serializer.data},
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {"message": "Error al registrar el pago.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request, pago_id):
        try:
            # Obtén el pago por su ID
            pago = Pago.objects.get(id=pago_id)
        except Pago.DoesNotExist:
            return Response(
                {"message": "Pago no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener el pedido relacionado al pago
        pedido = pago.id_pedido

        # Sumar el monto del pago eliminado al saldo pendiente del pedido
        pedido.outstanding_balance += pago.amount
        pedido.save()

        # Eliminar el pago
        pago.delete()

        return Response(
            {"message": "Pago eliminado exitosamente y saldo ajustado.", "saldo_pendiente": pedido.outstanding_balance},
            status=status.HTTP_200_OK
        )