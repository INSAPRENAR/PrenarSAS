from rest_framework import serializers
from api_prenar.models import Pago
import math
from django.db import models

class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__'

    def validate(self, data):
        pedido = data.get("id_pedido")
        monto = data.get("amount")

        if not pedido:
            raise serializers.ValidationError({"id_pedido": "El pedido es obligatorio."})

        monto = float(monto or 0)
        if monto <= 0:
            raise serializers.ValidationError({"amount": "El monto debe ser mayor que 0."})

        #Saldo REAL = total - sum(pagos)
        total_pagado = (
            Pago.objects
            .filter(id_pedido=pedido)
            .aggregate(s=models.Sum("amount"))
            .get("s") or 0
        )

        saldo_real = (pedido.total or 0) - total_pagado
        if saldo_real < 0:
            saldo_real = 0

        if saldo_real == 0:
            raise serializers.ValidationError("El pedido ya está completamente pagado.")

        if monto > saldo_real:
            raise serializers.ValidationError(
                f"El monto del pago ({monto}) supera el saldo pendiente del pedido ({saldo_real})."
            )

        return data

class PagoDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__' 