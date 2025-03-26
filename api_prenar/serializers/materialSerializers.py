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
    class Meta:
        model = CategoriaMaterial
        fields = '__all__'