from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.serializers.despachoSerializers import DespachoSerializer
from api_prenar.models import Pedido, Despacho, Producto, EstivaDevuelta
from collections import OrderedDict
from api_prenar.services.estivas import recalcular_remaining_estivas
from django.db import transaction, models
from rest_framework.exceptions import ValidationError

class DespachoView(APIView):

    def get(self, request, pedido_id):
        try:
            # Filtrar despachos por pedido_id
            despachos = Despacho.objects.filter(id_pedido=pedido_id)
            
            if not despachos:
                return Response(
                    {"message": "No hay despachos registrados para este pedido.", "data": []},
                    status=status.HTTP_200_OK
                )

            despachos_data = []
            for despacho in despachos:
                despacho_data = DespachoSerializer(despacho).data
                # Se asume que despacho_data['products'] es una lista de diccionarios con los datos de cada producto
                products = despacho_data.get("products", [])

                estivas_sent = sum([p.get("numero_estibas", 0) for p in products])

                despacho_data["estivas_sent"] = estivas_sent

                # Crear un resumen de los productos: nombre (referencia) y cantidad
                products_summary = ", ".join([
                    f"{p.get('name', 'Sin nombre')} (Ref: {p.get('referencia', '-')}, Cant: {p.get('cantidad', 0)})"
                    for p in products
                ])
                despacho_data["products_summary"] = products_summary
                despachos_data.append(despacho_data)

            return Response(
                {"message": "Despachos obtenidos exitosamente.", "data": despachos_data},
                status=status.HTTP_200_OK
            )

        except Pedido.DoesNotExist:
            return Response(
                {"message": f"No se encontró el pedido con ID {pedido_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": "Error al obtener los despachos.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    @transaction.atomic
    def post(self, request):
        serializer = DespachoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"message": "Error al registrar el despacho.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        pedido_id = serializer.validated_data['id_pedido'].id
        productos_despacho = serializer.validated_data['products']

        # 1) Agrupar por referencia:
        agrupados: dict[int, dict] = {}
        for prod in productos_despacho:
            ref = prod.get('referencia')
            cantidad = prod.get('cantidad', 0)
            if ref in agrupados:
                agrupados[ref]['cantidad'] += cantidad
            else:
                agrupados[ref] = {
                    **prod,
                    'cantidad': cantidad
                }

        try:
            pedido = Pedido.objects.get(id=pedido_id)

            # Obtener todos los despachos previos para este pedido,
            # y calcular sumas por referencia:
            despachos_previos = Despacho.objects.filter(id_pedido=pedido_id)
            despachado_por_ref: dict[int, int] = {}
            for d in despachos_previos:
                for dprod in d.products:
                    ref = dprod.get('referencia')
                    despachado_por_ref[ref] = despachado_por_ref.get(ref, 0) + dprod.get('cantidad', 0)

            # 2) Validar e imputar
            for ref, prod_despacho in agrupados.items():
                name = prod_despacho.get('name')
                color = prod_despacho.get('color')
                cantidad_nueva = prod_despacho['cantidad']

                # Buscar en el pedido original
                producto_en_pedido = next(
                    (p for p in pedido.products if p.get('referencia') == ref),
                    None
                )
                if not producto_en_pedido:
                    return Response(
                        {"message": f"No se encontró la referencia {ref} en el pedido."},
                        status=status.HTTP_404_NOT_FOUND
                    )

                solicitado = producto_en_pedido.get('cantidad_unidades', 0)
                ya_despachado = despachado_por_ref.get(ref, 0)

                # 3) Validación contra lo solicitado
                if ya_despachado + cantidad_nueva > solicitado:
                    return Response(
                        {
                            "message": (
                                f"La cantidad a despachar ({cantidad_nueva}) + ya despachadas ({ya_despachado}) "
                                f"excede las solicitadas ({solicitado}) para {name} {color}."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # 4) Actualizar el JSON del pedido in-memory
                producto_en_pedido['cantidades_despachadas'] = ya_despachado + cantidad_nueva

            # 5) Calcular estado final del pedido
            all_fully = all(
                p.get('cantidades_despachadas', 0) == p.get('cantidad_unidades', 0)
                for p in pedido.products
            )
            saldo_pendiente = (pedido.outstanding_balance or 0) > 0.0001

            # Solo COMPLETADO si está todo despachado y NO hay saldo pendiente
            pedido.state = 2 if (all_fully and not saldo_pendiente) else 1
            pedido.products = pedido.products  # marca modificado
            pedido.save()

            # 6) Crear el despacho
            despacho = serializer.save()
            # 7) IMPORTANTE: si ya existen estivas devueltas, recalcular el remaining_total
            recalcular_remaining_estivas(pedido_id)
            return Response(
                {
                    "message": "Despacho registrado exitosamente.",
                    "data": DespachoSerializer(despacho).data
                },
                status=status.HTTP_201_CREATED
            )

        except Pedido.DoesNotExist:
            return Response(
                {"message": f"No se encontró el pedido con ID {pedido_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": "Error al registrar el despacho.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @transaction.atomic
    def put(self, request, despacho_id):
        try:
            despacho = Despacho.objects.select_for_update().get(id=despacho_id)
            pedido_id = despacho.id_pedido_id

            estibas_old = self._estibas_en_despacho(despacho)

            # estibas nuevas vienen del request.data["products"]
            products_new = (request.data.get("products") or [])
            estibas_new = sum(int(p.get("numero_estibas") or 0) for p in products_new)

            # total prestadas actual (incluye este despacho)
            total_prestadas_actual = 0
            for d in Despacho.objects.filter(id_pedido_id=pedido_id).only("products"):
                total_prestadas_actual += sum(int(p.get("numero_estibas") or 0) for p in (d.products or []))

            # total prestadas si se modifica este despacho
            total_prestadas_mod = total_prestadas_actual - estibas_old + estibas_new
            if total_prestadas_mod < 0:
                total_prestadas_mod = 0

            total_devueltas = self._total_devueltas(pedido_id)

            if total_devueltas > total_prestadas_mod:
                return Response(
                    {
                        "message": (
                            "No se puede modificar este despacho porque dejaría inconsistencia "
                            "con el registro de las estivas devueltas. "
                            "Primero ajuste el registro de estivas devueltas en Resumen Pedido."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = DespachoSerializer(despacho, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            recalcular_remaining_estivas(pedido_id)

            return Response(
                {"message": "Despacho actualizado exitosamente.", "despacho": serializer.data},
                status=status.HTTP_200_OK
            )

        except ValidationError as ve:
            return Response({"message": "No se pudo actualizar.", "errors": ve.detail}, status=400)
    
    @staticmethod
    def _total_devueltas(pedido_id: int) -> int:
        return (
            EstivaDevuelta.objects
            .filter(id_pedido_id=pedido_id)
            .aggregate(s=models.Sum("estiva_amount_returned"))
            .get("s") or 0
        )

    @staticmethod
    def _estibas_en_despacho(despacho: Despacho) -> int:
        return sum(int(p.get("numero_estibas") or 0) for p in (despacho.products or []))
    
    @transaction.atomic
    def delete(self, request, despacho_id):
        try:
            # Bloquea el despacho para evitar carreras
            despacho = Despacho.objects.select_for_update().get(id=despacho_id)
            pedido = despacho.id_pedido
            pedido_id = pedido.id

            # 1) calcular estibas del despacho que se quiere borrar
            estibas_despacho = self._estibas_en_despacho(despacho)

            # 2) total estibas prestadas actuales (sum de todos los despachos)
            #    Reutilizamos tu función recalcular que internamente ya calcula total.
            #    Pero aquí necesitamos el total: lo calculamos directo (rápido y claro)
            total_prestadas_actual = 0
            despachos_pedido = Despacho.objects.filter(id_pedido_id=pedido_id).only("products")
            for d in despachos_pedido:
                total_prestadas_actual += sum(int(p.get("numero_estibas") or 0) for p in (d.products or []))

            # 3) total prestadas si se borra este despacho
            total_prestadas_sin = total_prestadas_actual - estibas_despacho
            if total_prestadas_sin < 0:
                total_prestadas_sin = 0  # por seguridad

            # 4) total devueltas registradas
            total_devueltas = self._total_devueltas(pedido_id)

            # 5) BLOQUEO: si ya devolvieron más de lo que quedaría prestado
            if total_devueltas > total_prestadas_sin:
                return Response(
                    {
                        "message": (
                            "No se puede eliminar este despacho porque dejaría inconsistencia "
                            "con el registro de las estivas devueltas. "
                            "Primero ajuste el registro de estivas devueltas en Resumen Pedido."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ===== SI PASA EL CHECK, AHÍ SÍ BORRAS =====

            # (tu lógica de revertir cantidades_despachadas)
            for despacho_prod in (despacho.products or []):
                referencia = despacho_prod.get("referencia")
                amount_despacho = despacho_prod.get("cantidad", 0)

                producto_encontrado = None
                for prod in (pedido.products or []):
                    if prod.get("referencia") == referencia:
                        producto_encontrado = prod
                        break

                if not producto_encontrado:
                    continue

                if "cantidades_despachadas" in producto_encontrado:
                    nuevo_valor = (producto_encontrado["cantidades_despachadas"] or 0) - (amount_despacho or 0)
                    producto_encontrado["cantidades_despachadas"] = max(nuevo_valor, 0)

            all_fully_dispatched = all(
                (prod.get("cantidad_unidades", 0) == prod.get("cantidades_despachadas", 0))
                for prod in (pedido.products or [])
            )
            pedido.state = 2 if all_fully_dispatched else 1
            pedido.products = pedido.products
            pedido.save()

            despacho.delete()

            # 6) recalcular remaining_total con el nuevo total de estibas despachadas
            recalcular_remaining_estivas(pedido_id)

            return Response(
                {"message": f"Despacho con ID {despacho_id} eliminado exitosamente."},
                status=status.HTTP_200_OK
            )

        except Despacho.DoesNotExist:
            return Response(
                {"message": f"Despacho con ID {despacho_id} no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as ve:
            # Si tu recalcular_remaining_estivas lanza ValidationError por cualquier razón
            return Response(
                {"message": "No se pudo completar la operación.", "errors": ve.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"message": "Error al intentar eliminar el despacho.", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )