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
                    # Se usa el campo "cantidad" del pedido (antes "cantidad_unidades")
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
                            {"message": f"La cantidad solicitada ({cantidad_despacho}) más las cantidades ya despachadas ({cantidad_despachada_total}) exceden las unidades solicitadas ({cantidad_disponible}) para el producto {referencia}."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Actualizar el campo 'cantidades_despachadas' en el JSON del producto correspondiente
                    if 'cantidades_despachadas' not in producto_encontrado:
                        producto_encontrado['cantidades_despachadas'] = 0
                    producto_encontrado['cantidades_despachadas'] += cantidad_despacho
                
                # Verificar si TODOS los productos del pedido están totalmente despachados
                all_fully_dispatched = True
                for prod in pedido.products:
                    cantidad_total = prod.get('cantidad', 0)
                    despachado = prod.get('cantidades_despachadas', 0)
                    if despachado < cantidad_total:
                        all_fully_dispatched = False
                        break
                if all_fully_dispatched:
                    pedido.state = 2
                
                # Guardar los cambios en el pedido
                pedido.products = pedido.products  # Marca el campo como modificado
                pedido.save()
                
                # Crear el despacho
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
    
    def delete(self, request, despacho_id):
        try:
            # Obtener el despacho por su ID
            despacho = Despacho.objects.get(id=despacho_id)

            # Obtener el producto relacionado
            producto = despacho.id_producto

            # Obtener el pedido relacionado
            pedido = despacho.id_pedido

            if not producto:
                return Response(
                    {"message": "El despacho no tiene un producto relacionado."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            producto.save()

            # Buscar el producto en el JSON de `products` del pedido
            producto_encontrado = None
            for prod in pedido.products:
                if prod['referencia'] == producto.id:  # Comparar con la referencia correcta
                    producto_encontrado = prod
                    break
            
            if not producto_encontrado:
                return Response(
                    {"message": f"No se encontró el producto con referencia {producto.id} en el pedido."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Restar el valor de `amount` al campo `cantidades_despachadas`
            if 'cantidades_despachadas' in producto_encontrado:
                producto_encontrado['cantidades_despachadas'] -= despacho.amount
                if producto_encontrado['cantidades_despachadas'] < 0:
                    producto_encontrado['cantidades_despachadas'] = 0  # Evitar valores negativos
            
            # Forzar el estado del pedido a 1
            pedido.state = 1

            # Guardar los cambios en el JSON y el estado
            pedido.products = pedido.products
            pedido.save()

            # Eliminar el despacho
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