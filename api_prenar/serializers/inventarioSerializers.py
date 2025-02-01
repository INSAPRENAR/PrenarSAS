from rest_framework import serializers
from api_prenar.models import Inventario, Despacho
from django.db.models import Sum
from django.db import transaction
from rest_framework.validators import UniqueValidator

class InventarioSerializer(serializers.ModelSerializer):
    cargo_number = serializers.CharField(
        max_length=255,
        validators=[
            UniqueValidator(
                queryset=Inventario.objects.all(),
                message="El número de orden de cargue ya se encuentra registrado."
            )
        ]
    )

    class Meta:
        model = Inventario
        fields = '__all__'

    def validate(self, data):
        """
        Validación para que las cantidades despachadas no superen las solicitadas.
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

        # Validar que la nueva producción no exceda la cantidad permitida en el pedido
        productos_pedido = pedido.products  # Asumiendo que 'products' es una lista de diccionarios
        producto_en_pedido = next((p for p in productos_pedido if p['referencia'] == producto.id), None)

        if not producto_en_pedido:
            raise serializers.ValidationError(f"El producto {producto.id} no está en el pedido {pedido.id}.")

        cantidad_permitida = producto_en_pedido['cantidad_unidades']

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

            # Actualizar la cantidad de almacén del producto
            if producto:
                # Si la producción es mayor a 0, sumamos a la cantidad de almacén
                if total_production > 0:
                    producto.warehouse_quantity += total_production
                
                # Si la salida es mayor a 0, restamos a la cantidad de almacén
                if total_output > 0:
                    producto.warehouse_quantity -= total_output

                # Validar que la cantidad en almacén no sea negativa
                if producto.warehouse_quantity < 0:
                    raise serializers.ValidationError(
                        f"La cantidad en almacén del producto {producto.name} no puede ser negativa."
                    )
                producto.save()

                # Calcular saldo_almacen
                saldo_almacen = producto.warehouse_quantity
                validated_data['saldo_almacen'] = saldo_almacen

            # Crear el registro de inventario
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