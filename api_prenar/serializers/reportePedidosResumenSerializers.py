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
            product["cantidad_entregar"] = cantidad_unidades - cantidades_despachadas
        return products
