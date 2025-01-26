from rest_framework import serializers
from api_prenar.models import Inventario, Despacho
from django.db.models import Sum
from django.db import transaction

class InventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventario
        fields = '__all__'

    def validate(self, data):
        """
        Validación para garantizar que la producción registrada no exceda la cantidad del pedido
        y que las cantidades despachadas no superen las solicitadas.
        """
        conformal_production = data.get('conformal_production', 0)
        not_comformal_production = data.get('not_comformal_production', 0)
        total_production = conformal_production + not_comformal_production
        conformal_output = data.get('comformal_output', 0)
        not_comformal_output = data.get('not_comformal_output', 0)
        total_output = conformal_output + not_comformal_output

        # Obtenemos el producto y el pedido relacionados
        producto = data.get('id_producto')
        pedido = data.get('id_pedido')

        if not producto:
            raise serializers.ValidationError("El campo 'id_producto' es obligatorio.")
        if not pedido:
            raise serializers.ValidationError("El campo 'id_pedido' es obligatorio.")

        # Validar que no se registren simultáneamente producción y salida
        if total_production > 0 and total_output > 0:
            raise serializers.ValidationError("No se puede registrar producción y salida al mismo tiempo.")

        # Calcular la producción acumulada para este producto y pedido
        produccion_acumulada = Inventario.objects.filter(
            id_producto=producto,
            id_pedido=pedido
        ).aggregate(total=Sum('total_production'))['total'] or 0

        # Validar que la nueva producción no exceda la cantidad permitida en el pedido
        productos_pedido = pedido.products  # Asumiendo que 'products' es una lista de diccionarios
        producto_en_pedido = next((p for p in productos_pedido if p['referencia'] == producto.id), None)

        if not producto_en_pedido:
            raise serializers.ValidationError(f"El producto {producto.id} no está en el pedido {pedido.id}.")

        cantidad_permitida = producto_en_pedido['cantidad_unidades']

        if produccion_acumulada + total_production > cantidad_permitida:
            raise serializers.ValidationError(
                f"La producción acumulada ({produccion_acumulada + total_production}) "
                f"supera la cantidad permitida del pedido ({cantidad_permitida})."
            )

        # Nueva Validación: Manejo de `total_output`
        if total_output > 0:
            # Calcular la cantidad despachada acumulada
            cantidad_despachada = Despacho.objects.filter(
                id_producto=producto,
                id_pedido=pedido
            ).aggregate(total=Sum('amount'))['total'] or 0

            # Calcular la cantidad total después del nuevo despacho
            cantidad_total_despacho = cantidad_despachada + total_output

            if cantidad_total_despacho > cantidad_permitida:
                raise serializers.ValidationError(
                    f"El valor a despachar ({cantidad_total_despacho}) supera la cantidad solicitada del pedido ({cantidad_permitida})."
                )

        return data

    def create(self, validated_data):
        """
        Cálculo y actualización de los campos totales y balance, incluyendo la cantidad de almacén del producto
        y la creación de registros en Despacho si corresponde.
        """
        with transaction.atomic():
            conformal_production = validated_data.get('conformal_production', 0)
            not_comformal_production = validated_data.get('not_comformal_production', 0)
            total_production = conformal_production + not_comformal_production

            conformal_output = validated_data.get('comformal_output', 0)
            not_comformal_output = validated_data.get('not_comformal_output', 0)
            total_output = conformal_output + not_comformal_output

            validated_data['total_production'] = total_production
            validated_data['total_output'] = total_output

            pedido = validated_data.get('id_pedido')
            producto = validated_data.get('id_producto')

            # Validar si 'products' es una lista de diccionarios
            if pedido and producto:
                products = pedido.products  # JSON de productos
                for prod in products:
                    if prod.get('referencia') == producto.id:  # Comparar por el campo de referencia
                        # Restar la producción al campo control
                        prod['control'] -= total_production
                        if prod['control'] < 0:
                            raise serializers.ValidationError(
                                f"La cantidad en control no puede ser negativa. Producto: {prod['name']}"
                            )
                        break  # Detener la búsqueda una vez encontrado el producto

                # Actualizar el campo products del pedido
                pedido.products = products
                pedido.save()

            # Actualizar la cantidad de almacén del producto
            if producto:
                # Si la producción es mayor a 0, sumamos a la cantidad de almacén
                if total_production > 0:
                    producto.warehouse_quantity += total_production

                # Validar que la cantidad en almacén no sea negativa
                if producto.warehouse_quantity < 0:
                    raise serializers.ValidationError(
                        f"La cantidad en almacén del producto {producto.name} no puede ser negativa."
                    )
                producto.save()

            # Crear el registro de inventario
            inventario = super().create(validated_data)

            return inventario

class InventarioSerializerInventario(serializers.ModelSerializer):
    # Campo adicional para mostrar el order_code del pedido
    order_code = serializers.CharField(source='id_pedido.order_code', read_only=True)
    name = serializers.CharField(source='id_producto.name', read_only=True)
    
    class Meta:
        model = Inventario
        # Listamos todos los campos del modelo Inventario y sumamos el campo order_code
        fields = [
            'id',
            'inventory_date',
            'id_producto',
            'id_pedido',
            'number_upload',
            'conformal_production',
            'not_comformal_production',
            'comformal_output',
            'not_comformal_output',
            'total_production',
            'total_output',
            'email_user',
            'registration_date',
            'order_code',
            'name'
        ]