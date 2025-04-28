from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.serializers.despachoSerializers import DespachoSerializer
from api_prenar.models import Pedido, Despacho, Producto
from collections import OrderedDict

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
            pedido.state = 2 if all_fully else 1
            pedido.products = pedido.products  # marca modificado
            pedido.save()

            # 6) Crear el despacho
            despacho = serializer.save()
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
    
    def put(self, request, despacho_id):
        try:
            despacho = Despacho.objects.get(id=despacho_id)
        except Despacho.DoesNotExist:
            return Response(
                {"message": "Despacho no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DespachoSerializer(despacho, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Despacho actualizado exitosamente.", "despacho": serializer.data},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"message": "Error al actualizar el despacho.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request, despacho_id):
        try:
            # Obtener el despacho por su ID
            despacho = Despacho.objects.get(id=despacho_id)
            pedido = despacho.id_pedido

            # Para cada producto incluido en el despacho,
            # se busca el correspondiente en el JSON de productos del pedido
            for despacho_prod in despacho.products:
                referencia = despacho_prod.get('referencia')
                amount_despacho = despacho_prod.get('cantidad', 0)

                # Buscar el producto en el JSON del pedido que coincida con la referencia
                producto_encontrado = None
                for prod in pedido.products:
                    if prod.get('referencia') == referencia:
                        producto_encontrado = prod
                        break

                if not producto_encontrado:
                    # Si no se encuentra el producto, se puede optar por continuar o retornar error.
                    # En este ejemplo se continúa con el siguiente producto.
                    continue

                # Restar el valor de "amount" del despacho al campo "cantidades_despachadas"
                if 'cantidades_despachadas' in producto_encontrado:
                    nuevo_valor = producto_encontrado['cantidades_despachadas'] - amount_despacho
                    # Evitar valores negativos
                    producto_encontrado['cantidades_despachadas'] = nuevo_valor if nuevo_valor >= 0 else 0

            # Validar si para todos los productos del pedido se cumple que:
            # cantidad_unidades <= cantidades_despachadas
            all_fully_dispatched = True
            for prod in pedido.products:
                if prod.get('cantidad_unidades', 0) != prod.get('cantidades_despachadas', 0):
                    all_fully_dispatched = False
                    break

            pedido.state = 2 if all_fully_dispatched else 1

            # Guardar los cambios del pedido y eliminar el despacho
            pedido.save()
            despacho.delete()

            return Response(
                {"message": f"Despacho con ID {despacho_id} eliminado exitosamente."},
                status=status.HTTP_200_OK
            )

        except Despacho.DoesNotExist:
            return Response(
                {"message": f"Despacho con ID {despacho_id} no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": "Error al intentar eliminar el despacho.", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )