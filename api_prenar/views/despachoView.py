from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.serializers.despachoSerializers import DespachoSerializer
from api_prenar.models import Pedido, Despacho, Producto

class DespachoView(APIView):

    def get(self, request, pedido_id):
        try:
            # Filtrar despachos por pedido_id y usar select_related para obtener el nombre del producto relacionado
            despachos = Despacho.objects.filter(id_pedido=pedido_id).select_related('id_producto')

            # Verificamos si no se encontraron despachos
            if not despachos:
                return Response(
                    {"message": "No hay despachos registrados para este pedido.", "data": []},
                    status=status.HTTP_200_OK
                )

            # Serializamos los despachos y también incluimos el nombre del producto
            despachos_data = []
            for despacho in despachos:
                despacho_data = DespachoSerializer(despacho).data
                # Añadir el nombre del producto al diccionario de datos del despacho
                despacho_data['id_producto_name'] = despacho.id_producto.name
                despachos_data.append(despacho_data)

            # Devolver los datos de los despachos
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
            id_pedido = serializer.validated_data['id_pedido'].id
            id_producto = serializer.validated_data['id_producto'].id
            amount = serializer.validated_data['amount']

            try:
                # Obtener el pedido relacionado
                pedido = Pedido.objects.get(id=id_pedido)

                # Validar que el producto existe en el campo 'products'
                producto_encontrado = None
                for producto in pedido.products:
                    if producto['referencia'] == id_producto:  # Comparar correctamente
                        producto_encontrado = producto
                        break

                if not producto_encontrado:
                    return Response(
                        {"message": f"No se encontró la referencia del producto {id_producto} en el pedido."},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Validar la cantidad total acumulada
                cantidad_disponible = producto_encontrado['cantidad_unidades']
                despachos_existentes = Despacho.objects.filter(id_pedido=id_pedido, id_producto=id_producto)
                cantidad_despachada = sum(despacho.amount for despacho in despachos_existentes)

                if cantidad_despachada + amount > cantidad_disponible:
                    return Response(
                        {
                            "message": f"La cantidad solicitada ({amount}) más las cantidades ya despachadas ({cantidad_despachada}) exceden las unidades solicitadas ({cantidad_disponible})."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Obtener el producto relacionado
                producto_model = Producto.objects.get(id=id_producto)

                # Validar que haya suficiente cantidad en almacén
                if producto_model.warehouse_quantity < amount:
                    return Response(
                        {
                            "message": f"La cantidad en almacén ({producto_model.warehouse_quantity}) no es suficiente para el despacho solicitado ({amount})."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Restar el valor de `amount` al campo `warehouse_quantity` del producto
                producto_model.warehouse_quantity -= amount
                producto_model.save()

                # Actualizar el campo 'cantidades_despachadas' en el JSON del producto correspondiente en el pedido
                if 'cantidades_despachadas' not in producto_encontrado:
                    producto_encontrado['cantidades_despachadas'] = 0
                producto_encontrado['cantidades_despachadas'] += amount

                # Verificar si TODOS los productos están totalmente despachados
                all_fully_dispatched = True
                for prod in pedido.products:  # Recorremos todos los productos del pedido
                    cantidad_unidades = prod.get('cantidad_unidades', 0)
                    cantidades_despachadas = prod.get('cantidades_despachadas', 0)
                    
                    # Si alguno no cumple que cantidades_despachadas == cantidad_unidades, no se cambia el estado
                    if cantidades_despachadas < cantidad_unidades:
                        all_fully_dispatched = False
                        break

                # Si todos están despachados, cambiar el estado del pedido a '2'
                if all_fully_dispatched:
                    pedido.state = 2

                # Guardar los cambios en el campo 'products' del modelo 'Pedido'
                pedido.products = pedido.products  # Esto marca el campo como modificado
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
                    {"message": f"No se encontró el pedido con ID {id_pedido}."},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Producto.DoesNotExist:
                return Response(
                    {"message": f"No se encontró el producto con ID {id_producto}."},
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

            # Sumar el valor de `amount` al campo `warehouse_quantity` del producto
            producto.warehouse_quantity += despacho.amount
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