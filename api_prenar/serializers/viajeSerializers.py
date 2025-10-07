from rest_framework import serializers
from api_prenar.models import Viaje, Pedido
from django.db.models import Q

class ViajeSerializer(serializers.ModelSerializer):
    class Meta:
        model= Viaje    
        fields= '__all__'

        # Estos los calculas tú; no deben venir en el POST
        read_only_fields = (
            'shipping_value',
            'sales_value',
            'product_value_balance',
            'shipping_value_balance',
            'shipping_value_paid',
            'returned_shipping_balance',
        )
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            pedido = instance.id_pedido  # FK cargada
            ref = instance.product
            item = None
            for p in (pedido.products or []):
                if p.get('referencia') == ref:
                    item = p
                    break
            if item:
                nombre = item.get('name') or ''
                color = item.get('color') or ''
                data['product'] = f"{nombre} - {color}".strip()
            else:
                # si no se encuentra, dejar el valor numérico como string (o None)
                data['product'] = str(ref) if ref is not None else None
            
             # ---- Extras del Pedido ----
            data['order_code']   = pedido.order_code
            data['trip_valor']   = float(pedido.trip_valor or 0.0)
            data['trip_number']  = int(pedido.trip_number or 0)

            # Nombre del cliente (desde id_client)
            data['client_name'] = getattr(pedido.id_client, 'name', None)

            # Suma de 'total' de todos los items del JSON 'products'
            products = pedido.products or []
            products_total_sum = 0.0
            for it in products:
                # usa 0.0 si no está la llave 'total' o si no es numérico
                try:
                    products_total_sum += float(it.get('total', 0) or 0)
                except (TypeError, ValueError):
                    pass
            data['products_total_sum'] = products_total_sum
            
        except Exception:
            # ante cualquier problema, mantener el valor original
            pass
        return data
    
    def validate(self, attrs):
        # --- 1) Obtener pedido y valores base ---
        pedido = attrs.get('id_pedido') or (self.instance and self.instance.id_pedido)
        if not pedido:
            raise serializers.ValidationError({"id_pedido": "id_pedido es requerido."})

        product = attrs.get('product') if 'product' in attrs else (self.instance and self.instance.product)
        if product is None:
            raise serializers.ValidationError({"product": "product es requerido."})

        total_product = attrs.get('total_product') if 'total_product' in attrs else (self.instance and self.instance.total_product) or 0

        # shipping_value por defecto = trip_valor del pedido
        if attrs.get('shipping_value') is None:
            attrs['shipping_value'] = float(pedido.trip_valor or 0.0)
        shipping_value = float(attrs.get('shipping_value') or 0.0)

        # --- 2) Calcular sales_value desde pedido.products ---
        # Buscar el item del JSON products cuyo 'referencia' == product
        item = None
        for p in pedido.products or []:
            if p.get('referencia') == product:
                item = p
                break

        if not item:
            raise serializers.ValidationError({"product": "El product no coincide con ningún item del pedido (referencia)."})

        vr_unitario = float(item.get('vr_unitario') or 0.0)
        vr_unitario_desc = float(item.get('vr_unitario_descuento') or 0.0)
        usar_descuento = bool(item.get('usar_descuento') or False)
        descuento_total = float(item.get('descuento_total') or 0.0)
        iva = float(item.get('iva') or 0.0)

        # Precio base según usar_descuento
        unit = vr_unitario_desc if usar_descuento else vr_unitario

        # Aplicar descuento si corresponde
        if descuento_total > 0:
            unit = unit * (1 - (descuento_total / 100.0))

        # Aplicar IVA si corresponde
        if iva > 0:
            unit = unit * (1 + (iva / 100.0))

        sales_value = unit * float(total_product or 0)
        attrs['sales_value'] = sales_value

        # --- 3) Saldos por producto (cadena por product) ---
        trip_total = float(pedido.trip_valor or 0.0) * float(pedido.trip_number or 0)

        # Buscar último viaje del mismo pedido y MISMO product (excluyendo self si es update)
        qs = Viaje.objects.filter(id_pedido=pedido, product=product).order_by('id')
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        last = qs.last()

        if last is None:
            # Primer viaje de este product
            attrs['product_value_balance'] = float(pedido.total or 0.0) - trip_total - sales_value
            attrs['shipping_value_balance'] = trip_total - shipping_value
            attrs['shipping_value_paid'] = shipping_value
        else:
            # Siguientes viajes del mismo product
            attrs['product_value_balance'] = float(last.product_value_balance or 0.0) - sales_value
            attrs['shipping_value_balance'] = float(last.shipping_value_balance or 0.0) - shipping_value
            attrs['shipping_value_paid'] = float(last.shipping_value_paid or 0.0) + shipping_value

        # --- 4) returned_shipping_balance (no negativo) ---
        shipping_sent = int(attrs.get('shipping_sent') or 0)
        returned_shipping = int(attrs.get('returned_shipping') or 0)
        rsb = shipping_sent - returned_shipping
        if rsb < 0:
            rsb = 0
        attrs['returned_shipping_balance'] = rsb

        return attrs