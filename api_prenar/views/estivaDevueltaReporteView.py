from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from rest_framework.pagination import PageNumberPagination

from api_prenar.models import Pedido
from api_prenar.serializers.estivaDevueltaReporteSerializers import ReporteEstivasDevueltaSerializer

class ReporteEstivasDevueltaView(APIView):
    def get(self, request):
        try:
            order_code = request.query_params.get("order_code")
            name_cliente = request.query_params.get("name_cliente")

            filters = Q()
            if order_code:
                filters &= Q(order_code__icontains=order_code)

            if name_cliente:
                filters &= Q(id_client__name__icontains=name_cliente)

            pedidos = (
                Pedido.objects
                .select_related("id_client")
                .prefetch_related("despachos")  # 👈 clave para sumar JSON sin N+1
                .filter(filters)
                .annotate(
                    estivas_devueltas=Coalesce(Sum("estivas__estiva_amount_returned"), 0)
                )
                .order_by("-id")  # o "-order_date" si lo tienes
            )

            if not pedidos.exists():
                return Response(
                    {"message": "No se encontraron registros con los filtros especificados."},
                    status=status.HTTP_200_OK
                )

            paginator = PageNumberPagination()
            paginator.page_size = 20
            paginated = paginator.paginate_queryset(pedidos, request)

            serializer = ReporteEstivasDevueltaSerializer(paginated, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {"message": "Error al obtener el resumen de estivas.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )