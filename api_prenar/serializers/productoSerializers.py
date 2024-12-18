from rest_framework import serializers
from api_prenar.models import Producto

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

    def validate(self, data):
        """
        Validaciones personalizadas para los datos del producto.
        """
        if data.get('unit_price', 0) <= 0:
            raise serializers.ValidationError("El precio unitario debe ser mayor a 0.")
        if data.get('discounted_unit_price', 0) < 0:
            raise serializers.ValidationError("El precio con descuento no puede ser negativo.")
        if data.get('warehouse_quantity', 0) < 0:
            raise serializers.ValidationError("La cantidad en el almacén no puede ser negativa.")
        return data