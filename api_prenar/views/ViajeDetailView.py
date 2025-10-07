from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Viaje
from api_prenar.serializers.viajeSerializers import ViajeSerializer

class ViajeDetailView(APIView):
    """
    Devuelve la información de un viaje específico por su ID.
    """
    def get(self, request, viaje_id=None):
        if not viaje_id:
            return Response(
                {"message": "Debe proporcionar el ID del viaje."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            viaje = Viaje.objects.get(pk=viaje_id)
        except Viaje.DoesNotExist:
            return Response(
                {"message": "Viaje no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ViajeSerializer(viaje)
        return Response(
            {
                "message": "Viaje obtenido exitosamente.",
                "viaje": serializer.data
            },
            status=status.HTTP_200_OK
        )