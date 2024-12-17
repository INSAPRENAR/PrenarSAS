from rest_framework import serializers
from api_prenar.models import Inventario

class InventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventario
        fields = '__all__'

    def validate(self, data):
        """
        Validación para garantizar que solo se registre producción o salida, no ambos.
        """
        conformal_production = data.get('conformal_production', 0)
        not_comformal_production = data.get('not_comformal_production', 0)
        comformal_output = data.get('comformal_output', 0)
        not_comformal_output = data.get('not_comformal_output', 0)

        # Obtenemos el producto relacionado
        producto = data.get('id_producto')
        if not producto:
            raise serializers.ValidationError("El campo 'id_producto' es obligatorio.")

        # Validar que no se registren simultáneamente producción y salida
        if (conformal_production > 0 or not_comformal_production > 0) and (comformal_output > 0 or not_comformal_output > 0):
            raise serializers.ValidationError("No se puede registrar producción y salida al mismo tiempo.")

        # Validar existencia suficiente para salida
        total_output = comformal_output + not_comformal_output
        if total_output > producto.warehouse_quantity:
            raise serializers.ValidationError(f"La salida total ({total_output}) supera las existencias actuales del producto ({producto.warehouse_quantity}).")

        return data

    def create(self, validated_data):
        """
        Cálculo y actualización de los campos totales y balance.
        """
        conformal_production = validated_data.get('conformal_production', 0)
        not_comformal_production = validated_data.get('not_comformal_production', 0)
        comformal_output = validated_data.get('comformal_output', 0)
        not_comformal_output = validated_data.get('not_comformal_output', 0)

        # Obtenemos el producto relacionado
        producto = validated_data['id_producto']

        # Calcular total de producción y salidas
        total_production = conformal_production + not_comformal_production
        total_output = comformal_output + not_comformal_output

        # Balance previo
        previous_balance = producto.warehouse_quantity

        # Actualizar balance y existencia del producto
        if total_production > 0:
            validated_data['balance'] = previous_balance + total_production
            producto.warehouse_quantity += total_production
        elif total_output > 0:
            validated_data['balance'] = previous_balance - total_output
            producto.warehouse_quantity -= total_output

        # Guardar totales calculados
        validated_data['total_production'] = total_production
        validated_data['total_output'] = total_output

        # Actualizar el producto
        producto.save()

        # Guardar el inventario
        return super().create(validated_data)