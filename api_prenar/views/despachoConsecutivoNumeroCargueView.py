from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Despacho
import re

class NextCargoNumberView(APIView):
    def get(self, request):
        # Tomar solo los cargo_number que empiecen por T seguido de dígitos (p.ej. T322)
        pattern = re.compile(r'^[Tt](\d+)$')  # case-insensitive para la T
        max_num = None

        # Evita cargar todos los campos del modelo
        for code in Despacho.objects.values_list('cargo_number', flat=True).iterator():
            if not code:
                continue
            m = pattern.match(str(code).strip())
            if m:
                n = int(m.group(1))
                if max_num is None or n > max_num:
                    max_num = n

        next_code = f"T{max_num + 1}" if max_num is not None else "T322"
        return Response({"next_cargo_number": next_code}, status=status.HTTP_200_OK)