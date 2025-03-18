from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Despacho, Pedido
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML

class OrdenCarguePDFView(APIView):
    def get(self, request, despacho_id):
        try:
            # Obtén el despacho usando el id del despacho
            despacho = Despacho.objects.get(id=despacho_id)
            # Con el id_pedido que viene en el despacho, obtén el pedido
            pedido = despacho.id_pedido

            # Ejemplo: supongamos que 'order_code' y 'client_name'
            # vienen del pedido y su cliente relacionado
            order_code = pedido.order_code
            client_name = pedido.id_client.name  # ajusta según tu modelo

            # Serializa 'products'
            # Asumiendo que despacho.products es una lista de objetos,
            # extraemos sus campos deseados.
            products = [{
                "lote": product.get('lote'),
                "name": product.get('name'),
                "color": product.get('color'),
                "cantidad": product.get('cantidad'),
                "referencia": product.get('referencia'),
                "numero_rotulo": product.get('numero_rotulo'),
                "numero_estibas": product.get('numero_estibas'),
            } for product in despacho.products]

            context = {
                "cargo_number": despacho.cargo_number,
                "dispatch_date": str(despacho.dispatch_date),
                "entry_time": despacho.entry_time,
                "departure_time": despacho.departure_time,
                "production_number": despacho.production_number,
                "rotulo_number": despacho.rotulo_number,
                "order_code": order_code,
                "client_name": client_name,
                "driver": despacho.driver,
                "driver_identification": despacho.driver_identification,
                "plate": despacho.plate,
                "vehicle_type": despacho.vehicle_type,
                "phone": despacho.phone,
                "products": products,
                "observation": despacho.observation,
                "dispatcher": despacho.dispatcher,
                "warehouseman": despacho.warehouseman,
            }

            html_string = render_to_string("api_prenar/orden_despacho.html", context)
            pdf_file = HTML(string=html_string).write_pdf()

            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="orden_cargue.pdf"'
            return response

        except Despacho.DoesNotExist:
            return Response({"message": "No existe despacho para ese ID."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": "Error generando PDF", "error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)