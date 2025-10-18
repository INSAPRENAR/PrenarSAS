from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api_prenar.models import CalendarioDespacho
from api_prenar.serializers.calendarioDespachoSerializers import CalendarioDespachoSerializer


class CalendarioDespachoDetailEspecificoView(APIView):
    
    def get(self, request, calendario_id):
        try:
            calendario = CalendarioDespacho.objects.get(id=calendario_id)
        except CalendarioDespacho.DoesNotExist:
            return Response(
                {"message": "Calendario no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CalendarioDespachoSerializer(calendario)
        return Response(
            {"message": "Calendario obtenido exitosamente", "Calendario": serializer.data},
            status=status.HTTP_200_OK
        )