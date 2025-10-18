from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api_prenar.models import Calendario
from api_prenar.serializers.calendarioSerializers import CalendarioSerializer


class CalendarioDetailEspecificoView(APIView):
    
    def get(self, request, calendario_id):
        try:
            calendario = Calendario.objects.get(id=calendario_id)
        except Calendario.DoesNotExist:
            return Response(
                {"message": "Calendario no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CalendarioSerializer(calendario)
        return Response(
            {"message": "Calendario obtenido exitosamente", "Calendario": serializer.data},
            status=status.HTTP_200_OK
        )