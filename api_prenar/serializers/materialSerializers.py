from rest_framework import serializers
from api_prenar.models import Material
from api_prenar.models.categoria_material import CategoriaMaterial

class MaterialSerializer(serializers.ModelSerializer):
    extentd = serializers.SerializerMethodField()
    def get_extentd(self, obj):
        # Retorna el valor legible del campo 'extent'
        return obj.get_extent_display()
    class Meta:
        model = Material
        fields = '__all__'

class CategoriaMaterialSerializer(serializers.ModelSerializer):
    extent_display = serializers.CharField(source='get_extent_display', read_only=True)
    class Meta:
        model = CategoriaMaterial
        fields = ['id', 'name', 'color', 'stock_quantity', 'extent', 'extent_display']