from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Viaje, Pedido
from api_prenar.serializers.viajeSerializers import ViajeSerializer
from django.db import transaction
from datetime import datetime

class ViajeCreateView(APIView):
    """
    Crea un Viaje. Todos los cálculos se realizan en el serializer.
    """
    def post(self, request):
        serializer = ViajeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            viaje = serializer.save()
            return Response(
                {"message": "Viaje creado exitosamente", "viaje": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"message": "Error al crear el viaje", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def get(self, request, pedido_id=None):
        """
        Obtiene todos los viajes relacionados con un pedido específico.
        """
        # 1) Validar parámetro
        if not pedido_id:
            return Response(
                {"message": "Debe proporcionar el ID del pedido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2) Verificar que el pedido exista
        try:
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            return Response(
                {"message": "Pedido no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3) Traer viajes del pedido (sin paginación)
        viajes = Viaje.objects.filter(id_pedido=pedido).order_by('id')

        # 4) Serializar y responder con el mismo formato
        serializer = ViajeSerializer(viajes, many=True)
        return Response(
            {
                "message": "Viajes obtenidos exitosamente." if viajes.exists() else "No hay viajes registrados para este pedido.",
                "viajes": serializer.data  # puede ser []
            },
            status=status.HTTP_200_OK
        )

    def delete(self, request, viaje_id):
        try:
            viaje = Viaje.objects.get(id=viaje_id)
        except Viaje.DoesNotExist:
            return Response(
                {"message": "Viaje no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        viaje.delete()
        return Response(
            {"message": "Viaje eliminado exitosamente."},
            status=status.HTTP_200_OK
        )

    def put(self, request, viaje_id: int):
        data = request.data or {}

        # 1) Buscar viaje
        try:
            viaje = Viaje.objects.select_related('id_pedido').get(id=viaje_id)
        except Viaje.DoesNotExist:
            return Response({"message": "Viaje no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        pedido = viaje.id_pedido

        date_str = data.get('date')
        new_date = None
        if date_str is not None:
            try:
                # acepta '' como "sin cambio"
                if date_str.strip() != '':
                    new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"message": "El campo date tiene un formato inválido. Use YYYY-MM-DD."},
                                status=status.HTTP_400_BAD_REQUEST)

        # invoice_fvsa (entero o null)
        raw_invoice = data.get('invoice_fvsa')
        new_invoice = None
        if raw_invoice is not None:
            inv = str(raw_invoice).strip()
            if inv == '':
                new_invoice = None
            else:
                # opcional: si quieres solo dígitos, valida:
                # if not inv.isdigit():
                #     return Response({"message": "El campo invoice_fvsa debe contener solo dígitos."},
                #                     status=status.HTTP_400_BAD_REQUEST)
                new_invoice = inv

        # shipping_sent (entero o null)
        raw_shipping_sent = data.get('shipping_sent')
        new_shipping_sent = None
        if raw_shipping_sent is not None and str(raw_shipping_sent).strip() != '':
            try:
                new_shipping_sent = int(raw_shipping_sent)
            except (TypeError, ValueError):
                return Response({"message": "El campo shipping_sent debe ser un entero."},
                                status=status.HTTP_400_BAD_REQUEST)

        # returned_shipping (entero o null)
        raw_returned_shipping = data.get('returned_shipping')
        new_returned_shipping = None
        if raw_returned_shipping is not None and str(raw_returned_shipping).strip() != '':
            try:
                new_returned_shipping = int(raw_returned_shipping)
            except (TypeError, ValueError):
                return Response({"message": "El campo returned_shipping debe ser un entero."},
                                status=status.HTTP_400_BAD_REQUEST)

        # 2) Validar/obtener total_product del payload
        if 'total_product' not in data:
            return Response(
                {"message": "Debe enviar el campo total_product."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            nuevo_total_product = int(data.get('total_product'))
        except (TypeError, ValueError):
            return Response(
                {"message": "El campo total_product debe ser un entero."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if nuevo_total_product <= 0:
            return Response(
                {"message": "El campo total_product debe ser mayor a 0."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3) Buscar el item del JSON products del pedido que coincide con la referencia (product)
        ref = viaje.product
        item = None
        for p in (pedido.products or []):
            if p.get('referencia') == ref:
                item = p
                break
        if not item:
            return Response(
                {"message": "El product del viaje no coincide con ningún item del pedido (referencia)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4) Calcular nuevo sales_value (misma lógica del POST)
        usar_descuento = bool(item.get('usar_descuento') or False)
        vr_unitario = float(item.get('vr_unitario') or 0.0)
        vr_unitario_desc = float(item.get('vr_unitario_descuento') or 0.0)
        descuento_total = float(item.get('descuento_total') or 0.0)
        iva = float(item.get('iva') or 0.0)

        unit = vr_unitario_desc if usar_descuento else vr_unitario
        if descuento_total > 0:
            unit *= (1 - (descuento_total / 100.0))
        if iva > 0:
            unit *= (1 + (iva / 100.0))

        nuevo_sales_value = unit * float(nuevo_total_product)

        # 5) Guardar el cambio en total_product y sales_value
        with transaction.atomic():
            # aplicar cambios simples si vienen
            update_fields = []

            if new_date is not None:
                viaje.date = new_date
                update_fields.append('date')

            if raw_invoice is not None:  # se envió algo ('' o valor)
                viaje.invoice_fvsa = new_invoice  # puede quedar None
                update_fields.append('invoice_fvsa')

            if raw_shipping_sent is not None:
                viaje.shipping_sent = new_shipping_sent  # puede None
                update_fields.append('shipping_sent')

            if raw_returned_shipping is not None:
                viaje.returned_shipping = new_returned_shipping  # puede None
                update_fields.append('returned_shipping')

            # total_product y sales_value (obligatorios en la operación)
            viaje.total_product = nuevo_total_product
            viaje.sales_value = nuevo_sales_value
            update_fields.extend(['total_product', 'sales_value'])

            # returned_shipping_balance = max(shipping_sent - returned_shipping, 0)
            # usando los "nuevos" (si no vinieron, usar los actuales)
            _sent = viaje.shipping_sent if new_shipping_sent is not None else (viaje.shipping_sent or 0)
            _ret = viaje.returned_shipping if new_returned_shipping is not None else (viaje.returned_shipping or 0)
            try:
                rsb = int(_sent or 0) - int(_ret or 0)
            except Exception:
                rsb = 0
            if rsb < 0:
                rsb = 0
            viaje.returned_shipping_balance = rsb
            update_fields.append('returned_shipping_balance')

            viaje.save(update_fields=update_fields)

            # Recalcular cadena balances de producto (mismo pedido y product) en orden ascendente por id
            cadena = list(Viaje.objects.filter(id_pedido=pedido, product=viaje.product).order_by('id'))

            # Índice del viaje modificado en la cadena
            try:
                idx = next(i for i, v in enumerate(cadena) if v.id == viaje.id)
            except StopIteration:
                serializer_one = ViajeSerializer(viaje)
                return Response(
                    {"message": "Viaje actualizado, pero no se pudo recomputar balances.", "viaje": serializer_one.data},
                    status=status.HTTP_200_OK
                )

            # Incluir transporte cuando el modificado es el primero
            trip_total = float(pedido.trip_valor or 0.0) * float(pedido.trip_number or 0.0)

            if idx == 0:
                # Base = total del pedido - (trip_valor * trip_number) - sales del primero
                base = float(pedido.total or 0.0) - trip_total - float(cadena[0].sales_value or 0.0)
                if cadena[0].product_value_balance != base:
                    cadena[0].product_value_balance = base
                    cadena[0].save(update_fields=['product_value_balance'])
                start = 1
            else:
                # Base para el modificado (no primero) = balance del anterior - sales actual
                base = float(cadena[idx - 1].product_value_balance or 0.0) - float(cadena[idx].sales_value or 0.0)
                if cadena[idx].product_value_balance != base:
                    cadena[idx].product_value_balance = base
                    cadena[idx].save(update_fields=['product_value_balance'])
                start = idx + 1  # recalcular a partir del siguiente

            # Cascada: nuevo_balance = balance_anterior - sales_value (para los siguientes)
            for i in range(start, len(cadena)):
                prev_balance = float(cadena[i - 1].product_value_balance or 0.0)
                nuevo_balance = prev_balance - float(cadena[i].sales_value or 0.0)
                if cadena[i].product_value_balance != nuevo_balance:
                    cadena[i].product_value_balance = nuevo_balance
                    cadena[i].save(update_fields=['product_value_balance'])

        # Respuesta (útil para refrescar la tabla en front)
        serializer = ViajeSerializer(cadena, many=True)
        return Response(
            {"message": "Viaje actualizado y balances recalculados.", "viajes": serializer.data},
            status=status.HTTP_200_OK
        )