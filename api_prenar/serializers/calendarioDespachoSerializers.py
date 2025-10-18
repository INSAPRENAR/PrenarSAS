from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from api_prenar.models import CalendarioDespacho, Pedido

from api_prenar.models import CalendarioDespacho

try:
    from api_prenar.models import Producto  # id, name, color, unit_price, discounted_unit_price
except Exception:
    Producto = None

class CalendarioListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarioDespacho
        fields = [
            'id',
            'start_date',
            'end_date',
            'dispatch',
            'observation',
            'email_user',
            'registration_date',
        ]

class DespachoItemSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    pedido_id = serializers.IntegerField(required=False, allow_null=True)  # puede venir null
    referencia = serializers.IntegerField()
    programacion_cantidad = serializers.IntegerField(min_value=0)
    produccion = serializers.IntegerField(min_value=0)

    # Calculados por el backend
    name = serializers.CharField(required=False, allow_blank=True)
    color = serializers.CharField(required=False, allow_blank=True)
    valor_unitario = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    total_programacion = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
    saldo = serializers.IntegerField(required=False)
    name_pedido = serializers.CharField(required=False, allow_blank=True)


class CalendarioDespachoSerializer(serializers.ModelSerializer):
    # Campo principal para despachos
    dispatch = DespachoItemSerializer(many=True)
    pending_dispatch_balance = serializers.JSONField(required=False)

    class Meta:
        model = CalendarioDespacho
        fields = [
            'id',
            'start_date',
            'end_date',
            'dispatch',
            'pending_dispatch_balance',
            'observation',
            'email_user',
            'registration_date',
        ]
        read_only_fields = ['pending_dispatch_balance', 'registration_date']

    # ----------------- Helpers -----------------
    def _money(self, value):
        """Redondeo a 2 decimales (Decimal)."""
        return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _get_product_from_order(self, pedido_id: int, referencia: int):
        """
        Busca el producto en Pedido.products por 'referencia'.
        Llaves esperadas en cada producto del pedido:
          referencia, name, color, vr_unitario, vr_unitario_descuento, descuento_total, iva
        """
        try:
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            raise serializers.ValidationError(f"Pedido {pedido_id} no existe.")

        prods = pedido.products
        if not isinstance(prods, list):
            raise serializers.ValidationError(
                f"El pedido {pedido_id} no tiene un JSON de productos válido."
            )

        for p in prods:
            if int(p.get('referencia', -1)) == int(referencia):
                return {
                    'name': p.get('name', ''),
                    'color': p.get('color', ''),
                    'vr_unitario': Decimal(p.get('vr_unitario', 0) or 0),
                    'vr_unitario_descuento': Decimal(p.get('vr_unitario_descuento', 0) or 0),
                    'descuento_total': Decimal(p.get('descuento_total', 0) or 0),  # %
                    'iva': Decimal(p.get('iva', 0) or 0),  # %
                    'order_code': pedido.order_code or '',
                }

        raise serializers.ValidationError(
            f"La referencia {referencia} no existe en los productos del pedido {pedido_id}."
        )

    def _get_product_from_catalog(self, referencia: int):
        """
        SIN PEDIDO: usa la 'referencia' como Producto.id del catálogo.
        Mapea: unit_price -> vr_unitario, discounted_unit_price -> vr_unitario_descuento.
        """
        if Producto is None:
            raise serializers.ValidationError(
                "No fue posible acceder al modelo de productos del catálogo (ver import de 'Producto')."
            )

        try:
            prod = Producto.objects.get(id=referencia)
        except Producto.DoesNotExist:
            raise serializers.ValidationError(f"Producto de catálogo con id={referencia} no existe.")

        unit_price = getattr(prod, 'unit_price', None)
        discounted_unit_price = getattr(prod, 'discounted_unit_price', None)

        return {
            'name': getattr(prod, 'name', ''),
            'color': getattr(prod, 'color', ''),
            'vr_unitario': Decimal(unit_price or 0),
            'vr_unitario_descuento': Decimal(discounted_unit_price or 0),
            'descuento_total': Decimal('0'),
            'iva': Decimal('0'),
        }

    def _compute_items_and_balance(self, items_in):
        """
        Recibe items validados (fecha=date, cantidades=int),
        calcula campos y devuelve:
          - items_out (JSON-friendly)
          - pending_balance (JSON-friendly) agrupado por referencia
        """
        items_out = []
        saldo_por_ref = {}

        for it in items_in:
            fecha = it['fecha']
            pedido_id = it.get('pedido_id', None)
            referencia = it['referencia']
            prog = int(it['programacion_cantidad'])
            prod_cant = int(it['produccion'])

            # Info de producto
            if pedido_id is not None:
                prod = self._get_product_from_order(pedido_id, referencia)
                order_code = prod.get('order_code', '')
            else:
                prod = self._get_product_from_catalog(referencia)
                order_code = ''

            base = prod['vr_unitario_descuento'] if prod['vr_unitario_descuento'] > 0 else prod['vr_unitario']

            # Descuento
            desc_pct = prod['descuento_total']
            val_desc = base * (Decimal('1') - (desc_pct / Decimal('100'))) if desc_pct > 0 else base

            # IVA
            iva_pct = prod['iva']
            val_final = val_desc * (Decimal('1') + (iva_pct / Decimal('100'))) if iva_pct > 0 else val_desc

            val_final = self._money(val_final)
            total_prog = self._money(val_final * Decimal(prog))
            saldo = prog - prod_cant

            # Agrupar saldo por referencia
            saldo_por_ref[referencia] = saldo_por_ref.get(referencia, 0) + saldo

            # JSON-friendly
            items_out.append({
                "fecha": fecha.isoformat(),
                "pedido_id": pedido_id,
                "referencia": referencia,
                "name": prod['name'],
                "color": prod['color'],
                "valor_unitario": float(val_final),
                "programacion_cantidad": prog,
                "total_programacion": float(total_prog),
                "produccion": prod_cant,  # aquí representa "despachado"
                "saldo": saldo,
                "name_pedido": order_code,
            })

        pending_balance = [
            {"referencia": ref, "total_general": total}
            for ref, total in saldo_por_ref.items()
        ]
        return items_out, pending_balance

    # ----------------- create -----------------
    def create(self, validated_data):
        items_in = validated_data.pop('dispatch', [])
        items_out, pending_balance = self._compute_items_and_balance(items_in)

        instance = CalendarioDespacho.objects.create(
            start_date=validated_data['start_date'],
            end_date=validated_data['end_date'],
            dispatch=items_out,                           # JSON puro
            pending_dispatch_balance=pending_balance,     # JSON puro
            observation=validated_data.get('observation', ''),
            email_user=validated_data['email_user'],
        )
        return instance

    # ----------------- update -----------------
    def update(self, instance, validated_data):
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.end_date = validated_data.get('end_date', instance.end_date)
        instance.observation = validated_data.get('observation', instance.observation)
        instance.email_user = validated_data.get('email_user', instance.email_user)

        if 'dispatch' in validated_data:
            items_in = validated_data['dispatch']
            items_out, pending_balance = self._compute_items_and_balance(items_in)
            instance.dispatch = items_out
            instance.pending_dispatch_balance = pending_balance

        instance.save()
        return instance