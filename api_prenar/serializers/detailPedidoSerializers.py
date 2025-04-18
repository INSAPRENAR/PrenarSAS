from rest_framework import serializers
from api_prenar.models import Pedido

class DetailPedidoEspecificoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = '__all__'