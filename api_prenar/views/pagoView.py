from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Pedido, Pago
from api_prenar.serializers.pagoSerializers import PagoSerializer, PagoDetalleSerializer
from api_prenar.services.pedidos import recalcular_saldo_y_estado_pedido
from django.db import transaction

class PagoView(APIView):

    def get(self, request, pedido_id=None):
        """
        Obtiene todos los pagos relacionados con un pedido específico.
        """
        if not pedido_id:
            return Response(
                {"message": "Debe proporcionar el ID del pedido."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Obtener el pedido por su ID
            pedido = Pedido.objects.get(id=pedido_id)

            # Filtrar los pagos relacionados con el pedido
            pagos = Pago.objects.filter(id_pedido=pedido)

            # Serializar los pagos
            serializer = PagoDetalleSerializer(pagos, many=True)

            return Response(
                {"message": "Pagos obtenidos exitosamente.", "pagos": serializer.data},
                status=status.HTTP_200_OK
            )
        except Pedido.DoesNotExist:
            return Response(
                {"message": "Pedido no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

    @transaction.atomic
    def post(self, request):
        serializer = PagoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"message": "Error al registrar el pago.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        pago = serializer.save()
        pedido = recalcular_saldo_y_estado_pedido(pago.id_pedido_id)

        return Response(
            {
                "message": "Pago registrado exitosamente.",
                "Pago": PagoSerializer(pago).data,
                "saldo_pendiente": pedido.outstanding_balance,
                "state": pedido.state,
            },
            status=status.HTTP_201_CREATED
        )
    
    @transaction.atomic
    def delete(self, request, pago_id):
        try:
            pago = Pago.objects.select_for_update().get(id=pago_id)
        except Pago.DoesNotExist:
            return Response({"message": "Pago no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        pedido_id = pago.id_pedido_id
        pago.delete()

        pedido = recalcular_saldo_y_estado_pedido(pedido_id)

        return Response(
            {
                "message": "Pago eliminado exitosamente y saldo ajustado.",
                "saldo_pendiente": pedido.outstanding_balance,
                "state": pedido.state,
            },
            status=status.HTTP_200_OK
        )