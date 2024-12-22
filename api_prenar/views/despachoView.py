from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.serializers.despachoSerializers import DespachoSerializer
from api_prenar.models import Pedido, Despacho, Producto

class DespachoView(APIView):
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

            if not producto:
                return Response(
                    {"message": "El despacho no tiene un producto relacionado."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Sumar el valor de `amount` al campo `warehouse_quantity` del producto
            producto.warehouse_quantity += despacho.amount
            producto.save()

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