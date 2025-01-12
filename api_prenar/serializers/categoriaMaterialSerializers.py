from rest_framework import serializers
from api_prenar.models.categoria_material import CategoriaMaterial

class CategoriaMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaMaterial
        fields = '__all__'