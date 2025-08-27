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
        - Actualiza cantidades del producto según inventario_type:
            1 -> warehouse_quantity_conforme
            2 -> warehouse_quantity_not_conforme
        - Calcula y guarda saldo_almacen en el registro de Inventario.
        - Si categoria == 1 e inventario_type == 1 y hay pedido:
            Suma producción acumulada y, si alcanza la cantidad solicitada, marca 'control=True' en el pedido.
        """
        with transaction.atomic():
            production = int(validated_data.get('production', 0) or 0)
            output = int(validated_data.get('output', 0) or 0)

            # Asegurarlos en validated_data por si vienen None
            validated_data['production'] = production
            validated_data['output'] = output

            producto = validated_data.get('id_producto')
            inventario_type = validated_data.get('inventory_type')  # 1=conforme, 2=no conforme
            categori = validated_data.get('categori')             # tu categoría de negocio (p.ej. 1=producción)
            pedido = validated_data.get('id_pedido')

            # Actualizar stock del producto según inventario_type
            if not producto:
                raise serializers.ValidationError("El campo 'id_producto' es obligatorio.")

            if inventario_type == 1:
                # Stock CONFORME
                if production > 0:
                    producto.warehouse_quantity_conforme += production
                if output > 0:
                    if producto.warehouse_quantity_conforme < output:
                        raise serializers.ValidationError(
                            f"La cantidad en almacén del producto {producto.name} "
                            f"({producto.warehouse_quantity_conforme}) es insuficiente para despachar {output} unidades."
                        )
                    producto.warehouse_quantity_conforme -= output
                validated_data['saldo_almacen'] = producto.warehouse_quantity_conforme

            elif inventario_type == 2:
                # Stock NO CONFORME
                if production > 0:
                    producto.warehouse_quantity_not_conforme += production
                if output > 0:
                    if producto.warehouse_quantity_not_conforme < output:
                        raise serializers.ValidationError(
                            f"La cantidad en almacén del producto {producto.name} "
                            f"({producto.warehouse_quantity_not_conforme}) es insuficiente para despachar {output} unidades."
                        )
                    producto.warehouse_quantity_not_conforme -= output
                validated_data['saldo_almacen'] = producto.warehouse_quantity_not_conforme

            else:
                raise serializers.ValidationError("El tipo de inventario no es válido.")

            # Guardar cambios de stock del producto
            producto.save()

            # Crear el registro de inventario
            inventario = super().create(validated_data)

            # --- Reglas de negocio extra: marcar control=True cuando corresponda ---
            # Solo aplica para categoria=1 (producción) e inventario_type=1 (conforme) con pedido presente.
            if pedido and categori == 1 and inventario_type == 1:
                # Sumar TODA la producción conforme (categoria=1, inventario_type=1) del producto para ese pedido
                total_produccion_conforme = (
                    Inventario.objects
                    .filter(
                        id_producto=producto,
                        id_pedido=pedido,
                        categori=1,
                        inventory_type=1
                    )
                    .aggregate(total=Sum('production'))['total'] or 0
                )

                # Buscar el item del producto dentro del JSON del pedido (por 'referencia')
                productos_pedido = pedido.products or []
                for item in productos_pedido:
                    if item.get('referencia') == producto.id:
                        cantidad_pedido = int(item.get('cantidad_unidades', 0) or 0)
                        # Si ya se cumplió (o superó) la cantidad, marcar control=True
                        if total_produccion_conforme >= cantidad_pedido:
                            if not item.get('control', False):
                                item['control'] = True
                                pedido.products = productos_pedido
                                pedido.save()
                        break
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

