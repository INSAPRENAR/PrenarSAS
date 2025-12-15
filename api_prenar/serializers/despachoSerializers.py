from rest_framework import serializers
from api_prenar.models import Despacho, Pedido
from collections import defaultdict
from django.db import transaction

class DespachoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Despacho
        fields = '__all__'
    
    def _sumar_por_referencia(self, products_list):
        acc = defaultdict(int)
        for p in (products_list or []):
            ref = p.get("referencia")
            cant = p.get("cantidad") or 0
            if ref is None:
                continue
            acc[int(ref)] += int(cant)
        return acc

    @transaction.atomic
    def update(self, instance, validated_data):
        old_sum = self._sumar_por_referencia(instance.products or [])
        new_products = validated_data.get("products", instance.products) or []
        new_sum = self._sumar_por_referencia(new_products)

        refs = set(old_sum.keys()) | set(new_sum.keys())
        delta = {ref: new_sum.get(ref, 0) - old_sum.get(ref, 0) for ref in refs}

        pedido_fk = validated_data.get("id_pedido", instance.id_pedido)
        if isinstance(pedido_fk, Pedido):
            pedido_id = pedido_fk.id
        else:
            pedido_id = int(pedido_fk)

        try:
            pedido = Pedido.objects.select_for_update().get(id=pedido_id)
        except Pedido.DoesNotExist:
            raise serializers.ValidationError({"id_pedido": f"No existe Pedido con id {pedido_id}"})

        pedido_products = pedido.products or []
        for item in pedido_products:
            ref = item.get("referencia")
            if ref is None:
                continue

            ref = int(ref)
            d = int(delta.get(ref, 0))
            if d == 0:
                continue

            actual = int(item.get("cantidades_despachadas") or 0)
            nuevo = actual + d
            if nuevo < 0:
                nuevo = 0

            # opcional: no permitir superar lo pedido
            maximo = int(item.get("cantidad_unidades") or 0)
            if maximo > 0 and nuevo > maximo:
                nuevo = maximo

            item["cantidades_despachadas"] = nuevo

        pedido.products = pedido_products
        pedido.save(update_fields=["products"])

        return super().update(instance, validated_data)