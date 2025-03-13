from rest_framework import serializers
from api_prenar.models import Pedido


class ReportePedidosResumenSerializer(serializers.ModelSerializer):
    client_name=serializers.CharField(source='id_client.name', read_only=True)
    value_paid = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()

    class Meta:
        model=Pedido
        fields=[
            'id',
            'client_name',
            'order_code',
            'order_date',
            'total',
            'state',
            'outstanding_balance',
            'value_paid',  
            'products'
        ]

    def get_value_paid(self, obj):
        return obj.total - obj.outstanding_balance
    
    def get_products(self, obj):
        products = obj.products  # Extraemos la lista de productos del JSONField
        for product in products:
            cantidad_unidades = product.get("cantidad_unidades", 0)
            cantidades_despachadas = product.get("cantidades_despachadas", 0)
            cantidad_entregar = cantidad_unidades - cantidades_despachadas
            product["cantidad_entregar"] = cantidad_entregar
            
            # Calculamos valor_unitario_pendientes según el campo usar_descuento
            if product.get("usar_descuento", False):
                # Si control es True, usamos vr_unitario_descuento
                product["valor_unidades_pendientes"] = cantidad_entregar * product.get("vr_unitario_descuento", 0)
            else:
                # Si control es False, usamos vr_unitario
                product["valor_unidades_pendientes"] = cantidad_entregar * product.get("vr_unitario", 0)
        return products
