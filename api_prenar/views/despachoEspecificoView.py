from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Despacho
from api_prenar.serializers.despachoSerializers import DespachoSerializer

class DespachoEspecificoView(APIView):
    def get(self, request, despacho_id):
        try:
            despacho_especifico=Despacho.objects.get(id=despacho_id)
            serializer=DespachoSerializer(despacho_especifico)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Despacho.DoesNotExist:
            return Response(
                {
                    "message":"despacho no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )