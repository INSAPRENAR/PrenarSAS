from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.serializers.despachoSerializers import DespachoSerializer
from api_prenar.models import Pedido, Despacho, Producto

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
        if serializer.is_valid():
            pedido_id = serializer.validated_data['id_pedido'].id
            # Se espera que el campo "products" sea una lista de diccionarios
            productos_despacho = serializer.validated_data['products']
            try:
                # Obtener el pedido relacionado
                pedido = Pedido.objects.get(id=pedido_id)
                # Iterar sobre cada producto a despachar
                for prod_despacho in productos_despacho:
                    referencia = prod_despacho.get('referencia')
                    name=prod_despacho.get('name')
                    color=prod_despacho.get('color')
                    cantidad_despacho = prod_despacho.get('cantidad')
                    
                    # Buscar el producto correspondiente en el JSON del pedido
                    producto_encontrado = None
                    for producto in pedido.products:
                        if producto.get('referencia') == referencia:
                            producto_encontrado = producto
                            break
                    if not producto_encontrado:
                        return Response(
                            {"message": f"No se encontró la referencia del producto {referencia} en el pedido."},
                            status=status.HTTP_404_NOT_FOUND
                        )
                    
                    # Validar la cantidad total acumulada
                    # Se usa el campo "cantidad_unidades" para determinar la cantidad solicitada
                    cantidad_disponible = producto_encontrado['cantidad_unidades']
                    
                    # Sumar la cantidad despachada previamente para este producto
                    despachos_existentes = Despacho.objects.filter(id_pedido=pedido_id)
                    cantidad_despachada_total = 0
                    for d in despachos_existentes:
                        for dprod in d.products:
                            if dprod.get('referencia') == referencia:
                                cantidad_despachada_total += dprod.get('cantidad', 0)
                    
                    if cantidad_despachada_total + cantidad_despacho > cantidad_disponible:
                        return Response(
                            {"message": f"La cantidad solicitada ({cantidad_despacho}) más las cantidades ya despachadas ({cantidad_despachada_total}) exceden las unidades solicitadas ({cantidad_disponible}) para el producto {name} {color}."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Actualizar el campo 'cantidades_despachadas' en el JSON del producto correspondiente
                    if 'cantidades_despachadas' not in producto_encontrado:
                        producto_encontrado['cantidades_despachadas'] = 0
                    producto_encontrado['cantidades_despachadas'] += cantidad_despacho
                
                # Verificar si TODOS los productos del pedido están totalmente despachados:
                # Es decir, para cada producto, la cantidad solicitada (cantidad) debe ser igual a las cantidades_despachadas.
                all_fully_dispatched = True
                for prod in pedido.products:
                    cantidad_total = prod.get('cantidad_unidades', 0)
                    despachado = prod.get('cantidades_despachadas', 0)
                    if despachado != cantidad_total:
                        all_fully_dispatched = False
                        break

                # Asignar el estado del pedido:
                # - 2 si se despachó exactamente la cantidad solicitada en todos los productos.
                # - 1 en caso contrario.
                pedido.state = 2 if all_fully_dispatched else 1

                # Marcar el campo "products" como modificado y guardar el pedido
                pedido.products = pedido.products
                pedido.save()
                
                # Crear y guardar el despacho
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
        # Datos inválidos
        return Response(
            {"message": "Error al registrar el despacho.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
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