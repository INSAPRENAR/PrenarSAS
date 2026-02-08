from django.db import transaction, models
from api_prenar.models import Pedido, Pago, Despacho

@transaction.atomic
def recalcular_saldo_y_estado_pedido(pedido_id: int) -> Pedido:
    pedido = Pedido.objects.select_for_update().get(id=pedido_id)

    # 1) Recalcular saldo: total - suma(pagos)
    total_pagado = (
        Pago.objects
        .filter(id_pedido_id=pedido_id)
        .aggregate(s=models.Sum("amount"))
        .get("s") or 0
    )

    nuevo_saldo = (pedido.total or 0) - total_pagado
    # Evitar negativos por redondeo o pagos extra
    if nuevo_saldo < 0:
        nuevo_saldo = 0

    pedido.outstanding_balance = nuevo_saldo

    # 2) Verificar si está totalmente despachado (usando tu JSON cantidades_despachadas)
    all_fully = all(
        (p.get("cantidades_despachadas", 0) == p.get("cantidad_unidades", 0))
        for p in (pedido.products or [])
    )

    # 3) Estado: completado solo si todo despachado y saldo 0
    saldo_pendiente = (pedido.outstanding_balance or 0) > 0
    pedido.state = 2 if (all_fully and not saldo_pendiente) else 1

    pedido.save(update_fields=["outstanding_balance", "state"])
    return pedido