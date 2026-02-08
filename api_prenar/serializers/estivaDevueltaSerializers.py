from rest_framework import serializers
from api_prenar.models import EstivaDevuelta

class EstivaDevueltaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstivaDevuelta
        fields = '__all__'
        read_only_fields = ("remaining_total",)