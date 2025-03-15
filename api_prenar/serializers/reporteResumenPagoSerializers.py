from rest_framework import serializers
from api_prenar.models import Pago

class ReporteResumenPagoSerializers(serializers.ModelSerializer):
    payment_method = serializers.CharField(source='get_payment_method_display', read_only=True)
    class Meta:
        model=Pago
        fields=[
            'id',
            'receipt_number',
            'payment_date',
            'amount',
            'payment_method'
        ]