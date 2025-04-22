from rest_framework import serializers
from api_prenar.models import Inventario, Despacho
from django.db.models import Sum
from django.db import transaction
from rest_framework.validators import UniqueValidator

class InventarioSerializer(serializers.ModelSerializer):
    cargo_number = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
    )
    saldo_almacen = serializers.IntegerField(read_only=True)
    total_production = serializers.IntegerField(read_only=True)
    total_output = serializers.IntegerField(read_only=True)

    class Meta:
        model = Inventario
        fields = '__all__'

    def validate(self, data):
        """
        Validación para que las cantidades despachadas no superen las solicitadas.
        """
        # Calcular totales de producción y salida
        production = data.get('production', 0)
        output = data.get('output', 0)

        # Obtener el producto (obligatorio)
        producto = data.get('id_producto')
        if not producto:
            raise serializers.ValidationError("El campo 'id_producto' es obligatorio.")

        # Obtener el pedido; puede ser nulo
        pedido = data.get('id_pedido')

        # Si se proporciona un pedido, se realizan las validaciones adicionales
        if pedido is not None:
            # No se permite registrar producción y salida simultáneamente
            if production > 0 and output > 0:
                raise serializers.ValidationError("No se puede registrar producción y salida al mismo tiempo.")

            # Validar que el producto esté en el pedido
            # Se asume que 'pedido.products' es una lista de diccionarios con las claves 'referencia', 'cantidad_unidades', etc.
            productos_pedido = pedido.products  
            producto_en_pedido = next((p for p in productos_pedido if p['referencia'] == producto.id), None)
            if not producto_en_pedido:
                raise serializers.ValidationError(
                    f"El producto {producto.name} {producto.color} no está en el pedido {pedido.order_code}."
                )

            cantidad_permitida = producto_en_pedido['cantidad_unidades']

            # Validación para salidas: verificar que la suma acumulada de salidas no supere la cantidad permitida
            if output > 0:
                total_output_acumulado = (
                    Inventario.objects.filter(id_producto=producto, id_pedido=pedido)
                    .aggregate(total=Sum('output'))['total'] or 0
                )
                total_output_final = total_output_acumulado + output
                if total_output_final > cantidad_permitida:
                    raise serializers.ValidationError(
                        f"El total de salidas acumuladas para el producto {producto.name} ({total_output_final}) supera la cantidad solicitada del pedido ({cantidad_permitida})."
                    )
        # Si pedido es nulo, se omiten las validaciones dependientes del pedido.
        return data

    def create(self, validated_data):
        """
        Se actualizan las cantidades en almacén dependiendo del tipo de inventario:
         - Si inventory_type es 1 se suma/resta a warehouse_quantity_conforme.
         - Si inventory_type es 2 se suma/resta a warehouse_quantity_not_conforme.
        Además, se actualiza el saldo_almacen del registro inventario.
        """
        with transaction.atomic():
            # Obtenemos las cantidades indicadas en la data, por ejemplo desde el request.
            production = validated_data.get('production', 0)
            output = validated_data.get('output', 0)
            
            # Se asignan a los campos del modelo (production y output) del inventario.
            validated_data['production'] = production
            validated_data['output'] = output

            # Obtenemos el producto y el tipo de inventario
            producto = validated_data.get('id_producto')
            inventory_type = validated_data.get('inventory_type')

            if producto:
                if inventory_type == 1:
                    # Producción: se suma al stock conforme
                    if production > 0:
                        producto.warehouse_quantity_conforme += production
                    # Salida: se resta del stock conforme con validación
                    if output > 0:
                        if producto.warehouse_quantity_conforme < output:
                            raise serializers.ValidationError(
                                f"La cantidad en almacén del producto {producto.name} ({producto.warehouse_quantity_conforme}) es insuficiente para despachar {output} unidades."
                            )
                        producto.warehouse_quantity_conforme -= output
                    # Se guarda el saldo en el inventario según la cantidad conforme actualizada
                    validated_data['saldo_almacen'] = producto.warehouse_quantity_conforme
                elif inventory_type == 2:
                    # Producción: se suma al stock NO conforme
                    if production > 0:
                        producto.warehouse_quantity_not_conforme += production
                    # Salida: se resta del stock NO conforme con validación
                    if output > 0:
                        if producto.warehouse_quantity_not_conforme < output:
                            raise serializers.ValidationError(
                                f"La cantidad en almacén del producto {producto.name} ({producto.warehouse_quantity_not_conforme}) es insuficiente para despachar {output} unidades."
                            )
                        producto.warehouse_quantity_not_conforme -= output
                    # Se guarda el saldo en el inventario según la cantidad no conforme actualizada
                    validated_data['saldo_almacen'] = producto.warehouse_quantity_not_conforme
                else:
                    raise serializers.ValidationError("El tipo de inventario no es válido.")

                # Se guarda la instancia del producto con los nuevos valores actualizados.
                producto.save()

            inventario = super().create(validated_data)
            return inventario

class InventarioSerializerInventario(serializers.ModelSerializer):
    # Campo adicional para mostrar el order_code del pedido
    order_code = serializers.CharField(source='id_pedido.order_code', read_only=True)
    name = serializers.CharField(source='id_producto.name', read_only=True)
    name_cliente = serializers.CharField(source='id_pedido.id_client.name', read_only=True)
    almacen_producto=serializers.IntegerField(source='id_producto.warehouse_quantity_conforme')
    color_producto=serializers.CharField(source='id_producto.color', read_only=True)
    inventory_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventario
        # Listamos todos los campos del modelo Inventario y sumamos el campo order_code
        fields = [
            'id',
            'inventory_date',
            'id_producto',
            'id_pedido',
            'production',
            'output',
            'inventory_type',
            'categori',
            'lote',
            'label_number_estiva',
            'production_order',
            'transporter_name',
            'observation',
            'email_user',
            'registration_date',
            'order_code',
            'name',
            'color_producto',
            'name_cliente',
            'saldo_almacen',
            'inventory_type_display',
            'almacen_producto',
            'cargo_number'
        ]
    def get_inventory_type_display(self, obj):
        # Django automáticamente genera el método get_FIELD_display() para campos con choices.
        return obj.get_inventory_type_display()

class InventarioSerializerInventarioDos(serializers.ModelSerializer):
    # Campo adicional para mostrar el order_code del pedido
    order_code = serializers.CharField(source='id_pedido.order_code', read_only=True)
    name = serializers.CharField(source='id_producto.name', read_only=True)
    name_cliente = serializers.CharField(source='id_pedido.id_client.name', read_only=True)
    almacen_producto=serializers.IntegerField(source='id_producto.warehouse_quantity_not_conforme')
    color_producto=serializers.CharField(source='id_producto.color', read_only=True)
    inventory_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventario
        # Listamos todos los campos del modelo Inventario y sumamos el campo order_code
        fields = [
            'id',
            'inventory_date',
            'id_producto',
            'id_pedido',
            'production',
            'output',
            'inventory_type',
            'categori',
            'lote',
            'label_number_estiva',
            'production_order',
            'transporter_name',
            'observation',
            'email_user',
            'registration_date',
            'order_code',
            'name',
            'color_producto',
            'name_cliente',
            'saldo_almacen',
            'inventory_type_display',
            'almacen_producto',
            'cargo_number'
        ]
    def get_inventory_type_display(self, obj):
        # Django automáticamente genera el método get_FIELD_display() para campos con choices.
        return obj.get_inventory_type_display()

