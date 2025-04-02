from rest_framework.views import APIView
from api_prenar.serializers.reporteResumenPagoSerializers import ReporteResumenPagoSerializers
from api_prenar.models import Pago
from rest_framework import status
from rest_framework.response import Response
from django.db.models import Q
from collections import defaultdict
from rest_framework.pagination import PageNumberPagination

class ReporteResumenPagoView(APIView):
    def get(self, request):
        try:
            # Obtener parámetros de búsqueda desde la URL
            order_code = request.query_params.get('order_code', None)
            start_date = request.query_params.get('start_date', None)
            end_date = request.query_params.get('end_date', None)
            name_cliente = request.query_params.get('name_cliente', None)

            # Construcción dinámica de los filtros usando Q()
            filters = Q()
            if order_code:
                filters &= Q(id_pedido__order_code__icontains=order_code)
            if name_cliente:
                filters &= Q(id_pedido__id_client__name__icontains=name_cliente)
            if start_date and end_date:
                filters &= Q(id_pedido__order_date__gte=start_date, id_pedido__order_date__lte=end_date)
            elif start_date:
                filters &= Q(id_pedido__order_date__gte=start_date)
            elif end_date:
                filters &= Q(id_pedido__order_date__lte=end_date)

            # Filtrar los pagos aplicando los filtros y ordenarlos (por ejemplo, por fecha de pago)
            pagos = Pago.objects.filter(filters).order_by('-id')

            # Si no se encuentran registros, se retorna un mensaje
            if not pagos.exists():
                return Response(
                    {"message": "No se encontraron pagos con los filtros especificados."},
                    status=status.HTTP_200_OK
                )

            # Agrupar los pagos por order_code usando un diccionario
            grupos = defaultdict(list)
            for pago in pagos:
                key = pago.id_pedido.order_code
                grupos[key].append(pago)

            # Construir la respuesta agrupada
            resultado = []
            for order_code, pagos_group in grupos.items():
                pedido = pagos_group[0].id_pedido  # Se usa el primer pago para obtener datos del pedido
                serializer = ReporteResumenPagoSerializers(pagos_group, many=True)
                grupo_data = {
                    "order_code": order_code,
                    "date_order": pedido.order_date,
                    "client_name": pedido.id_client.name,
                    "valor_total": pedido.total,
                    "payments": serializer.data,
                    "total_amount": sum(pago.amount for pago in pagos_group)
                }
                resultado.append(grupo_data)

            # Aplicar paginación a la lista de grupos
            paginator = PageNumberPagination()
            paginator.page_size = 20  # Ajusta el tamaño de página según lo necesites
            paginated_result = paginator.paginate_queryset(resultado, request)
            return paginator.get_paginated_response(paginated_result)

        except Exception as e:
            return Response(
                {"message": "Error al obtener los pagos.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )