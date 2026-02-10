from rest_framework import serializers
from api_prenar.models import Pedido, Despacho

class ReporteEstivasDevueltaSerializer(serializers.ModelSerializer):
    order_code = serializers.CharField()
    name_cliente = serializers.CharField(source="id_client.name", read_only=True)

    # viene del annotate
    estivas_devueltas = serializers.IntegerField(read_only=True)

    total_estiva_enviadas = serializers.SerializerMethodField()
    saldo_estiva = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = [
            "id",
            "order_code",
            "name_cliente",
            "estivas_devueltas",
            "total_estiva_enviadas",
            "saldo_estiva",
        ]

    def get_total_estiva_enviadas(self, obj: Pedido) -> int:
        """
        Suma de numero_estibas desde Despacho.products (JSON) para este pedido.
        Usamos obj.despachos.all() (prefetch) para que sea eficiente.
        """
        total = 0
        for d in obj.despachos.all():  # gracias a prefetch_related
            for p in (d.products or []):
                total += int(p.get("numero_estibas") or 0)
        return total

    def get_saldo_estiva(self, obj: Pedido) -> int:
        enviadas = self.get_total_estiva_enviadas(obj)
        devueltas = int(getattr(obj, "estivas_devueltas", 0) or 0)
        return max(enviadas - devueltas, 0)