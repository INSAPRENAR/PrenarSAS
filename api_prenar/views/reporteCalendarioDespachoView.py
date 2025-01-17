from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Calendario

class CalendarioDespachoStateDetalleView(APIView):
    def get(self, request):
        try:
            # Filtrar calendarios con type=1 y state=2
            calendarios = Calendario.objects.filter(type=2, state=2).select_related('id_pedido', 'id_producto')

            # Construir la respuesta
            calendarios_data = [
                {
                    "calendar_date": calendario.calendar_date,
                    "type": calendario.type,
                    "expected_date": calendario.expected_date,
                    "amount": calendario.amount,
                    "state": calendario.state,
                    "order_code": calendario.id_pedido.order_code if calendario.id_pedido else None,
                    "product_name": calendario.id_producto.name if calendario.id_producto else None,
                    "product_color": calendario.id_producto.color if calendario.id_producto else None,
                }
                for calendario in calendarios
            ]

            return Response(
                {
                    "message": "Calendarios de tipo 2 con estado 2 obtenidos exitosamente.",
                    "calendarios": calendarios_data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "message": "Error al obtener los calendarios de tipo 2 con estado 2.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )