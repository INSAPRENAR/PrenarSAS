from rest_framework import serializers
from api_prenar.models import Pedido

class PedidoCompletadosListaGeneralSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='id_client.name', read_only=True)
    class Meta:
        model=Pedido
        fields='__all__'