from rest_framework import serializers
from api_prenar.models import ConsumoMaterial

class ConsumoMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsumoMaterial
        fields = '__all__'