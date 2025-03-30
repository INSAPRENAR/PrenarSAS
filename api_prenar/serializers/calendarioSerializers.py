from rest_framework import serializers
from api_prenar.models import Calendario

class CalendarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calendario
        fields = '__all__'

class CalendarioTipo1Serializer(serializers.ModelSerializer):
    order_code = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    color_producto=serializers.SerializerMethodField()
    class Meta:
        model = Calendario
        fields = ['id','calendar_date', 'expected_date', 'id_pedido','order_code', 'id_producto','name','color_producto', 'amount', 'machine', 'state', 'observation']
    def get_order_code(self, obj):
        return obj.id_pedido.order_code if obj.id_pedido else None
    def get_name(self, obj):
        return obj.id_producto.name if obj.id_producto else None
    def get_color_producto(self, obj):
        return obj.id_producto.color if obj.id_producto else None

class CalendarioTipo2Serializer(serializers.ModelSerializer):
    order_code = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    color_producto=serializers.SerializerMethodField()
    class Meta:
        model = Calendario
        fields = ['id','calendar_date', 'expected_date', 'id_pedido', 'order_code', 'id_producto','name','color_producto', 'amount', 'dispatch_time', 'state', 'observation']
    def get_order_code(self, obj):
        return obj.id_pedido.order_code if obj.id_pedido else None
    def get_name(self, obj):
        return obj.id_producto.name if obj.id_producto else None
    def get_color_producto(self, obj):
        return obj.id_producto.color if obj.id_producto else None
