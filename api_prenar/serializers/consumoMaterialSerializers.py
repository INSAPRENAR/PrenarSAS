from rest_framework import serializers
from api_prenar.models import ConsumoMaterial

class ConsumoMaterialSerializer(serializers.ModelSerializer):
    # Usamos SerializerMethodField para obtener el 'name' de las relaciones
    id_categoria_name = serializers.SerializerMethodField()
    id_producto_name = serializers.SerializerMethodField()
    id_producto_color = serializers.SerializerMethodField()

    class Meta:
        model = ConsumoMaterial
        fields = '__all__'

    def get_id_categoria_name(self, obj):
        # Devuelve el nombre de la categoría
        return obj.id_categoria.name if obj.id_categoria else None

    def get_id_producto_name(self, obj):
        # Devuelve el nombre del producto
        return obj.id_producto.name if obj.id_producto else None
    
    def get_id_producto_color(self, obj):
        # Devuelve el nombre del producto
        return obj.id_producto.color if obj.id_producto else None