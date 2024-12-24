from rest_framework import serializers
from api_prenar.models import Pago

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
        
        # Verifica que el monto no exceda el saldo pendiente
        if validated_data['amount'] > pedido.outstanding_balance:
            raise serializers.ValidationError("El monto del pago excede el saldo pendiente del pedido.")
        
        # Actualiza el saldo pendiente del pedido
        pedido.outstanding_balance -= validated_data['amount']
        pedido.save()


        # Crea y retorna el registro de pago
        return super().create(validated_data)

class PagoDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__' 