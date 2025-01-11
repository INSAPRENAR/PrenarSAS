from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Calendario
from api_prenar.serializers.calendarioSerializers import CalendarioSerializer

class CalendarioEspecificoView(APIView):
    def get(self, request, calendario_id):
        try:
            calendario_especifico=Calendario.objects.get(id=calendario_id)
            serializer=CalendarioSerializer(calendario_especifico)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Calendario.DoesNotExist:
            return Response(
                {
                    "message":"calendario no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request, calendario_id):
        try:
            calendario_especifico = Calendario.objects.get(id=calendario_id)
        except Calendario.DoesNotExist:
            return Response(
                {
                    "message": "Calendario no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Aquí se actualizan los campos del producto utilizando el serializer
        serializer = CalendarioSerializer(calendario_especifico, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # Guarda los cambios
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)