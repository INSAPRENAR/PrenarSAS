from rest_framework import serializers
from api_prenar.models import Pedido

class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = '__all__'
    
    def validate_products(self, products):
        """
        Valida y calcula el total para cada producto y el total general.
        El cálculo se realiza de la siguiente forma:
        
        1. Si el campo 'iva' es mayor a 0:
           - Se verifica si 'iva_aplicado_vr_unitario' es True:
             - Si es verdadero, se aplica el IVA sobre 'vr_unitario'
             - Si es falso, se aplica el IVA sobre 'vr_unitario_descuento'
           - Se multiplica el precio con IVA por 'cantidad_unidades'.
           - Si 'descuento_total' es mayor a 0, se aplica el descuento.
        
        2. Si el campo 'iva' es menor o igual a 0:
           - Se multiplica:
             - 'vr_unitario' * 'cantidad_unidades' si 'usar_descuento' es False, o
             - 'vr_unitario_descuento' * 'cantidad_unidades' si 'usar_descuento' es True.
           - Si 'descuento_total' es mayor a 0, se aplica el descuento.
        """
        total_general = 0

        for product in products:
            cantidad = product.get('cantidad_unidades', 0)
            usar_descuento = product.get('usar_descuento', False)
            iva = product.get('iva', 0)
            descuento_total = product.get('descuento_total', 0)
            
            if not cantidad:
                raise serializers.ValidationError("Cada producto debe tener 'cantidad_unidades' válida.")
            
            # Cálculo según el valor de IVA
            if iva > 0:
                # Se revisa el campo booleano que indica dónde se aplica el IVA
                if product.get('iva_aplicado_vr_unitario', False):
                    base_price = product.get('vr_unitario')
                else:
                    base_price = product.get('vr_unitario_descuento')
                    
                if not base_price:
                    raise serializers.ValidationError("Cada producto debe tener un precio válido.")
                
                precio_con_iva = base_price * (1 + iva / 100)
                product_total = precio_con_iva * cantidad
            else:
                # Si IVA no es mayor a 0, se toma el precio según 'usar_descuento'
                if usar_descuento:
                    base_price = product.get('vr_unitario_descuento')
                else:
                    base_price = product.get('vr_unitario')
                    
                if not base_price:
                    raise serializers.ValidationError("Cada producto debe tener un precio válido.")
                
                product_total = base_price * cantidad

            # Se aplica el descuento si corresponde
            if descuento_total and descuento_total > 0:
                product_total = product_total - (product_total * (descuento_total / 100))
            
            product['total'] = product_total
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