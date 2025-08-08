from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Despacho

class NextCargoNumberView(APIView):
    def get(self, request):
        # Obtener todos los cargo_number que sean numéricos
        numeros = []

        for despacho in Despacho.objects.all():
            try:
                numeros.append(int(despacho.cargo_number))
            except ValueError:
                # Ignorar los que no sean numéricos
                pass

        if numeros:
            siguiente_numero = max(numeros) + 1
        else:
            # Si no hay números válidos en la base, empezamos desde 317
            siguiente_numero = 317

        return Response({"next_cargo_number": str(siguiente_numero)}, status=status.HTTP_200_OK)