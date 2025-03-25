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
        conformal_production = data.get('conformal_production', 0)
        not_comformal_production = data.get('not_comformal_production', 0)
        total_production = conformal_production + not_comformal_production

        conformal_output = data.get('comformal_output', 0)
        not_comformal_output = data.get('not_comformal_output', 0)
        total_output = conformal_output + not_comformal_output

        # Obtener el producto y pedido relacionados
        producto = data.get('id_producto')
        pedido = data.get('id_pedido')

        if not producto:
            raise serializers.ValidationError("El campo 'id_producto' es obligatorio.")
        if not pedido:
            raise serializers.ValidationError("El campo 'id_pedido' es obligatorio.")

        # No se permite registrar producción y salida simultáneamente
        if total_production > 0 and total_output > 0:
            raise serializers.ValidationError("No se puede registrar producción y salida al mismo tiempo.")

        # Validar que el producto esté en el pedido y obtener la cantidad permitida
        # Se asume que 'pedido.products' es una lista de diccionarios con las claves 'referencia' y 'cantidad_unidades'
        productos_pedido = pedido.products
        producto_en_pedido = next((p for p in productos_pedido if p['referencia'] == producto.id), None)
        if not producto_en_pedido:
            raise serializers.ValidationError(f"El producto {producto.id} no está en el pedido {pedido.id}.")

        cantidad_permitida = producto_en_pedido['cantidad_unidades']

        # Nueva validación para salidas:
        # Si se registra salida, se obtiene la suma acumulada de salidas en inventario para ese producto,
        # se le suma el total de salida que se está intentando registrar y se verifica que no supere la cantidad permitida.
        if total_output > 0:
            total_output_acumulado = (
                Inventario.objects.filter(id_producto=producto)
                .aggregate(total=Sum('total_output'))['total'] or 0
            )
            total_output_final = total_output_acumulado + total_output
            if total_output_final > cantidad_permitida:
                raise serializers.ValidationError(
                    f"El total de salidas acumuladas para el producto {producto.id} ({total_output_final}) supera la cantidad solicitada del pedido ({cantidad_permitida})."
                )

        return data

    def create(self, validated_data):
        """
        Cálculo y actualización de los totales y saldo, actualizando además el stock (warehouse_quantity) del producto.
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

            producto = validated_data.get('id_producto')

            if producto:
                # Si se registra producción, se suma al stock
                if total_production > 0:
                    producto.warehouse_quantity += total_production
                # Si se registra salida, se valida y se resta del stock
                if total_output > 0:
                    if producto.warehouse_quantity < total_output:
                        raise serializers.ValidationError(
                            f"La cantidad en almacén del producto {producto.name} ({producto.warehouse_quantity}) es insuficiente para despachar {total_output} unidades."
                        )
                    producto.warehouse_quantity -= total_output

                producto.save()
                # Asignar saldo_almacen según el stock actual del producto
                saldo_almacen = producto.warehouse_quantity
                validated_data['saldo_almacen'] = saldo_almacen

            inventario = super().create(validated_data)
            return inventario

class InventarioSerializerInventario(serializers.ModelSerializer):
    # Campo adicional para mostrar el order_code del pedido
    order_code = serializers.CharField(source='id_pedido.order_code', read_only=True)
    name = serializers.CharField(source='id_producto.name', read_only=True)
    name_cliente = serializers.CharField(source='id_pedido.id_client.name', read_only=True)
    almacen_producto=serializers.IntegerField(source='id_producto.warehouse_quantity')
    
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
            'name',
            'name_cliente',
            'saldo_almacen',
            'almacen_producto'
        ]