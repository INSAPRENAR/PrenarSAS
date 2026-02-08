from django.db import transaction
from rest_framework import serializers
from api_prenar.models import Despacho, EstivaDevuelta, Pedido


def calcular_total_estibas_despachadas(pedido_id: int) -> int:
    """
    Suma TOTAL de numero_estibas dentro del JSONField products de Despacho,
    para todos los despachos del pedido.
    """
    total = 0
    despachos = Despacho.objects.filter(id_pedido_id=pedido_id)  # ForeignKey en Despacho

    for d in despachos:
        for prod in (d.products or []):
            total += int(prod.get("numero_estibas") or 0)

    return total


@transaction.atomic
def recalcular_remaining_estivas(pedido_id: int) -> None:
    """
    Recalcula remaining_total para TODOS los registros de EstivaDevuelta de ese pedido,
    en orden de creación (id asc). Si algún registro deja remaining negativo, lanza error.
    """
    # validar que exista el pedido
    if not Pedido.objects.filter(id=pedido_id).exists():
        raise serializers.ValidationError({"id_pedido": f"Pedido {pedido_id} no existe."})

    total_estibas = calcular_total_estibas_despachadas(pedido_id)

    registros = (
        EstivaDevuelta.objects
        .select_for_update()
        .filter(id_pedido_id=pedido_id)
        .order_by("id")
    )

    restante = total_estibas

    for r in registros:
        dev = int(r.estiva_amount_returned or 0)

        if dev < 0:
            raise serializers.ValidationError({"estiva_amount_returned": "No puede ser negativo."})

        if dev > restante:
            # Caso 1: ya no hay estivas por devolver (restante=0)
            if restante == 0:
                raise serializers.ValidationError({
                    "estiva_amount_returned": (
                        f"El pedido ya completó el registro de la cantidad de estivas prestadas. "
                        f"El total de estivas prestadas son {total_estibas}."
                    )
                })

            # Caso 2: todavía hay, pero se pasó
            raise serializers.ValidationError({
                "estiva_amount_returned": (
                    f"La cantidad de estivas devueltas ({dev}) supera el saldo disponible ({restante}). "
                    f"El total de estivas prestadas son {total_estibas}."
                )
            })

        restante = restante - dev

        # guardar remaining_total
        if r.remaining_total != restante:
            r.remaining_total = restante
            r.save(update_fields=["remaining_total"])