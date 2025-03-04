from rest_framework import serializers
from api_prenar.models import Cliente

class ClienteSerializer(serializers.ModelSerializer):
    pedidos_pendientes = serializers.IntegerField(read_only=True)
    class Meta:
        model = Cliente
        fields = '__all__'

class ClienteDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

    