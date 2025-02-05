from rest_framework import serializers
from api_prenar.models import Pedido

class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = '__all__'
    
    def validate_products(self, products):
        """
        Valida y calcula el total para cada producto y el total general.
        """
        total_general = 0

        for product in products:
            cantidad = product.get('cantidad_unidades', 0)
            usar_descuento = product.get('usar_descuento', False)
            unit_price = (
                product.get('vr_unitario_descuento') if usar_descuento 
                else product.get('vr_unitario')
            )

            if not cantidad or not unit_price:
                raise serializers.ValidationError("Cada producto debe tener 'cantidad' y un precio válido.")

            # Calcula el total para el producto
            product_total = cantidad * unit_price
            product['total'] = product_total

            # Suma al total general
            total_general += product_total

        self.context['total_general'] = total_general  # Almacena el total general en el contexto
        return products

    def create(self, validated_data):
        # Recupera el total general calculado
        validated_data['total'] = self.context.get('total_general', 0)
        return super().create(validated_data)
    
    def validate_order_code(self, value):
        """
        Valida que el order_code no esté duplicado.
        """
        if Pedido.objects.filter(order_code=value).exists():
            raise serializers.ValidationError("El 'order_code' ya está registrado.")
        return value

class ListaNumerosPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = ['id', 'order_code']

class PedidoSerializerControlProduccion(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = '__all__'