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
        overall_discount = obj.total_discount_ordered or 0
        for product in products:
            cantidad_unidades = product.get("cantidad_unidades", 0)
            cantidades_despachadas = product.get("cantidades_despachadas", 0)
            cantidad_entregar = cantidad_unidades - cantidades_despachadas
            product["cantidad_entregar"] = cantidad_entregar

            if cantidad_entregar == 0:
                product["valor_unidades_pendientes"] = 0
            else:
                # Selecciona el precio base dependiendo de si se usa descuento
                if product.get("usar_descuento", False):
                    base_price = product.get("vr_unitario_descuento", 0)
                else:
                    base_price = product.get("vr_unitario", 0)

                # Si hay IVA, se suma al precio base
                iva = product.get("iva", 0)
                if iva:
                    base_price += base_price * (iva / 100)

                # Calcular el total multiplicando el precio base (con IVA) por la cantidad a entregar
                total_price = cantidad_entregar * base_price

                # Si hay descuento_total (mayor a 0), se le resta del total
                descuento_total = product.get("descuento_total", 0)
                if descuento_total > 0:
                    total_price -= total_price * (descuento_total / 100)
                
                # Aplica además el descuento global total_discount_ordered si es mayor a 0
                if overall_discount > 0:
                    total_price -= total_price * (overall_discount / 100)

                product["valor_unidades_pendientes"] = total_price
        return products
