from rest_framework import serializers
from api_prenar.models import Pedido, Pago
from django.db.models import Sum
from decimal import Decimal, ROUND_DOWN, getcontext

def trunc_float(value, decimals=2):
        factor = 10 ** decimals
        return int(value * factor) / factor

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
            

            # Truncamiento a float con dos decimales sin redondear
            product['total'] = trunc_float(product_total)
            total_general += trunc_float(product_total)

        self.context['total_general'] = total_general  # Almacena el total general en el contexto
        return products

    def create(self, validated_data):
        # Recupera el total general calculado en validate_products
        total_general = self.context.get('total_general', 0)
        # Obtiene el porcentaje de descuento ordenado (total_discount_ordered)
        descuento = validated_data.get('total_discount_ordered', 0)
        if descuento and descuento > 0:
            # Calcula el total aplicando el descuento porcentual
            total_general = total_general - (total_general * (descuento / 100))
        
        # Truncar el total general a dos decimales sin redondear
        total_general = trunc_float(total_general)
        validated_data['total'] = total_general
        validated_data['outstanding_balance'] = total_general
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

class PedidoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = '__all__'

    def validate(self, data):
        total_calculado = 0.0
        todos_despachados = True

        for producto in data.get('products', []):
            cantidad_unidades = producto.get('cantidad_unidades', 0)
            cantidades_despachadas = producto.get('cantidades_despachadas', 0)

            # Validación de cantidades
            if cantidad_unidades < cantidades_despachadas:
                raise serializers.ValidationError(
                    f"El valor de 'cantidad_unidades' no puede ser menor que 'cantidades_despachadas' para el producto {producto.get('name')}"
                )

            vr_unitario = producto.get('vr_unitario', 0.0)
            vr_unitario_descuento = producto.get('vr_unitario_descuento', 0.0)
            usar_descuento = producto.get('usar_descuento', False)
            iva = producto.get('iva', 0.0)
            iva_aplicado_vr_unitario = producto.get('iva_aplicado_vr_unitario', False)
            iva_aplicado_unitario_descuento = producto.get('iva_aplicado_unitario_descuento', False)
            descuento_total = producto.get('descuento_total', 0.0)

            # Calculamos el precio a aplicar
            vr_unitario_a_usar = vr_unitario_descuento if usar_descuento else vr_unitario

            # Aplicamos IVA
            if iva > 0:
                if iva_aplicado_vr_unitario:
                    vr_unitario_a_usar += vr_unitario * (iva / 100)
                elif iva_aplicado_unitario_descuento:
                    vr_unitario_a_usar += (vr_unitario_descuento * (iva / 100))

            # Calculamos el total del producto
            total_producto = cantidad_unidades * vr_unitario_a_usar

            # Aplicamos el descuento total
            descuento_total_aplicado = total_producto * (descuento_total / 100)
            total_producto -= descuento_total_aplicado

            # Acumulamos el total
            total_calculado += total_producto

            # Verificamos si todos los productos están despachados
            if cantidad_unidades != cantidades_despachadas:
                todos_despachados = False

        # Descuento global
        total_discount_ordered = data.get('total_discount_ordered', 0)
        if total_discount_ordered > 0:
            descuento_general= total_calculado * (total_discount_ordered / 100)
            total_calculado -= descuento_general

        # Actualización del estado
        if todos_despachados:
            data['state'] = 2  # Todos los productos están despachados
        else:
            data['state'] = 1  # Al menos un producto no está despachado

        # Truncar a dos decimales sin redondear
        total_truncado = Decimal(total_calculado).quantize(Decimal('0.00'), rounding=ROUND_DOWN)
        data['total'] = float(total_truncado)

        return data