from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import EstivaDevuelta, Pedido
from api_prenar.serializers.estivaDevueltaSerializers import EstivaDevueltaSerializer
from api_prenar.services.estivas import recalcular_remaining_estivas
from django.db import transaction

class EstivaDevueltaView(APIView):
    def get(self, request, pedido_id):
        if not pedido_id:
            return Response(
                {"message": "Debe proporcionar el ID del pedido."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Obtener el pedido por su ID
            pedido = Pedido.objects.get(id=pedido_id)

            # Filtrar los pagos relacionados con el pedido
            estiva = EstivaDevuelta.objects.filter(id_pedido=pedido)

            # Serializar los pagos
            serializer = EstivaDevueltaSerializer(estiva, many=True)

            return Response(
                {"message": "Estivas Devueltas obtenidos exitosamente.", "estivas": serializer.data},
                status=status.HTTP_200_OK
            )
        except Pedido.DoesNotExist:
            return Response(
                {"message": "Pedido no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @transaction.atomic
    def post(self, request):
        serializer = EstivaDevueltaSerializer(data=request.data)
        
        if not serializer.is_valid():
            print("ESTIVA DEVUELTA ERRORS:", serializer.errors)
            print("PAYLOAD:", request.data)
            return Response(
                {"message": "Error al registrar la estiva devuelta.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 👇 guarda con remaining_total temporal en 0
        estiva = serializer.save(remaining_total=0)

        # 👇 si id_pedido es FK, usa estiva.id_pedido_id (int)
        #    si id_pedido es IntegerField, esto también funciona con estiva.id_pedido
        pedido_id = getattr(estiva, "id_pedido_id", estiva.id_pedido)

        recalcular_remaining_estivas(pedido_id)

        estiva.refresh_from_db()
        return Response(
            {
                "message": "Estiva devuelta registrada exitosamente.",
                "estiva": EstivaDevueltaSerializer(estiva).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @transaction.atomic
    def put(self, request, estiva_id):
        try:
            instance = EstivaDevuelta.objects.select_for_update().get(id=estiva_id)
        except EstivaDevuelta.DoesNotExist:
            return Response({"message": "EstivaDevuelta no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = EstivaDevueltaSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            estiva = serializer.save()
            recalcular_remaining_estivas(estiva.id_pedido)
            estiva.refresh_from_db()

            return Response(
                {"message": "Estiva devuelta actualizada exitosamente.", "estiva": EstivaDevueltaSerializer(estiva).data},
                status=status.HTTP_200_OK
            )

        return Response(
            {"message": "Error al actualizar la estiva devuelta.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    @transaction.atomic
    def delete(self, request, estiva_id):
        try:
            instance = EstivaDevuelta.objects.select_for_update().get(id=estiva_id)
        except EstivaDevuelta.DoesNotExist:
            return Response({"message": "EstivaDevuelta no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        pedido_id = instance.id_pedido_id
        instance.delete()

        # recalcular cadena luego de borrar
        recalcular_remaining_estivas(pedido_id)

        return Response(
            {"message": "Estiva devuelta eliminada exitosamente."},
            status=status.HTTP_200_OK
        )
                