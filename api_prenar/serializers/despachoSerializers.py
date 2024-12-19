from rest_framework import serializers
from api_prenar.models import Despacho

class DespachoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Despacho
        fields = '__all__'