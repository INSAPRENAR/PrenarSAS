from rest_framework import serializers
from api_prenar.models import Pedido

class PedidoSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()  # Campo adicional para devolver el nombre del cliente

    class Meta:
        model = Pedido
        fields = '__all__'  # Incluye todos los campos del modelo
        extra_fields = ['client_name']  # Campo adicional que agregamos

    def get_client_name(self, obj):
        """
        Retorna el nombre del cliente relacionado.
        """
        return obj.id_client.name  # Accede al nombre del cliente relacionado