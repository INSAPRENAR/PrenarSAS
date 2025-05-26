from rest_framework import serializers
from api_prenar.models import Pago
import math

class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__'

    def validate(self, data):
        # Obtenemos el pedido relacionado
        pedido = data.get('id_pedido')
        monto_pago = data.get('amount')

        if not pedido:
            raise serializers.ValidationError("El pedido es obligatorio.")
        
        # Verificamos si el saldo pendiente es 0 y el monto del pago es mayor que 0
        if pedido.outstanding_balance == 0 and monto_pago > 0:
            raise serializers.ValidationError("El pedido ya está completamente pagado.")

        # Verificamos si el monto del pago supera el saldo pendiente
        if monto_pago > pedido.outstanding_balance:
            raise serializers.ValidationError(
                f"El monto del pago ({monto_pago}) supera el saldo pendiente del pedido ({pedido.outstanding_balance})."
            )
            

        return data

    def create(self, validated_data):
        # Obtiene el pedido relacionado con el pago
        pedido = validated_data['id_pedido']
        monto: float = validated_data['amount']

        # Calcula el nuevo saldo en bruto
        raw_saldo = pedido.outstanding_balance - monto
        
        # Trunca a 2 decimales (sin redondeo)
        nuevo_saldo = math.floor(raw_saldo * 100) / 100.0

        pedido.outstanding_balance = nuevo_saldo
        pedido.save()

        return super().create(validated_data)

class PagoDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__' 