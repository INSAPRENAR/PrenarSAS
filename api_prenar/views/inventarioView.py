from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.serializers.inventarioSerializers import InventarioSerializer
from api_prenar.serializers.inventarioSerializers import InventarioSerializerInventario, InventarioSerializerInventarioDos
from api_prenar.models import Inventario, GeneracionPassword
from django.db import transaction
from api_prenar.models import Inventario

class InventarioView(APIView):

    def get(self, request):
        try:
            
            inventarios = Inventario.objects.all().order_by("id_producto")
            agrupado_por_producto = {}

            for inventario in inventarios:
                producto = inventario.id_producto
                if producto.id not in agrupado_por_producto:
                    agrupado_por_producto[producto.id] = {
                        "id":producto.id,
                        "referencia": producto.product_code,  # Usar product_code si no tienes reference
                        "nombre_producto": producto.name,
                        "color": producto.color  # Agregar el campo color
                    }

            resultado = list(agrupado_por_producto.values())

            return Response(
                {"message": "Inventario agrupado por producto obtenido exitosamente.", "data": resultado},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(f"Error: {e}")
            return Response(
                {"message": "Error al obtener el inventario agrupado por producto.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        serializer=InventarioSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(
                    {"message":"Inventario registrado exitosamente", "data": serializer.data},
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"message":"Error al registrar el inventario", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(
            {"message":"Error al registrar el inventario", "error": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request, inventario_id=None):
        if not inventario_id:
            return Response(
                {"message": "Debe proporcionar el ID del inventario a eliminar."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener la contraseña del cuerpo de la solicitud
        password = request.data.get('password')
        if not password:
            return Response(
                {"message": "La contraseña es requerida para eliminar el inventario."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener la instancia de GeneracionPassword para comparar
        generacion = GeneracionPassword.objects.first()
        if not generacion:
            return Response(
                {"message": "La contraseña generada no está configurada en el sistema."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Verificar la contraseña proporcionada con la del modelo
        if password != generacion.password_generation:
            return Response(
                {"message": "Contraseña incorrecta."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Buscar el registro de inventario
            inventario = Inventario.objects.get(id=inventario_id)
            # Obtener el producto relacionado
            producto = inventario.id_producto

            with transaction.atomic():
                # Verificar el tipo de inventario y ajustar el stock correspondiente
                if inventario.inventory_type == 1:
                    # Para inventario conforme:
                    if inventario.production > 0:
                        producto.warehouse_quantity_conforme -= inventario.production
                    elif inventario.output > 0:
                        producto.warehouse_quantity_conforme += inventario.output

                    # Validar que la cantidad no sea negativa
                    if producto.warehouse_quantity_conforme < 0:
                        return Response(
                            {"message": f"La cantidad en almacén del producto {producto.name} no puede ser negativa."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                elif inventario.inventory_type == 2:
                    # Para inventario no conforme:
                    if inventario.production > 0:
                        producto.warehouse_quantity_not_conforme -= inventario.production
                    elif inventario.output > 0:
                        producto.warehouse_quantity_not_conforme += inventario.output

                    # Validar que la cantidad no sea negativa
                    if producto.warehouse_quantity_not_conforme < 0:
                        return Response(
                            {"message": f"La cantidad en almacén del producto {producto.name} no puede ser negativa."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                else:
                    return Response(
                        {"message": "El tipo de inventario no es válido."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Guardar los cambios en el producto
                producto.save()
                # Eliminar el registro de inventario
                inventario.delete()

            return Response(
                {"message": "Registro de inventario eliminado exitosamente."},
                status=status.HTTP_200_OK
            )
        except Inventario.DoesNotExist:
            return Response(
                {"message": f"No se encontró el registro de inventario con ID {inventario_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al intentar eliminar el registro de inventario.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, inventario_id):
        # Obtener la contraseña del cuerpo de la solicitud
        password = request.data.get('password')
        if not password:
            return Response(
                {"message": "La contraseña es requerida para eliminar el inventario."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener la instancia de GeneracionPassword para comparar
        generacion = GeneracionPassword.objects.first()
        if not generacion:
            return Response(
                {"message": "La contraseña generada no está configurada en el sistema."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Verificar la contraseña proporcionada con la del modelo
        if password != generacion.password_generation:
            return Response(
                {"message": "Contraseña incorrecta."},
                status=status.HTTP_403_FORBIDDEN
            )
    # Todo el flujo bajo una transacción
        with transaction.atomic():
            # 1) Bloquear el registro DENTRO del atomic
            try:
                inventario = (Inventario.objects
                            .select_for_update()
                            .select_related("id_producto")
                            .get(id=inventario_id))
            except Inventario.DoesNotExist:
                return Response({"message": "Inventario no encontrado."},
                                status=status.HTTP_404_NOT_FOUND)

            # 2) inventory_type obligatorio
            inventory_type = request.data.get('inventory_type', None)
            if inventory_type is None:
                return Response({"message": "Debe enviar 'inventory_type' en el payload."},
                                status=status.HTTP_400_BAD_REQUEST)
            try:
                inv_type = int(inventory_type)
            except (TypeError, ValueError):
                return Response({"message": "'inventory_type' debe ser un número."},
                                status=status.HTTP_400_BAD_REQUEST)

            if inv_type == 1:
                serializer_class = InventarioSerializerInventario
            elif inv_type == 2:
                serializer_class = InventarioSerializerInventarioDos
            else:
                return Response({"message": "Valor de 'inventory_type' inválido. Debe ser 1 o 2."},
                                status=status.HTTP_400_BAD_REQUEST)

            # 3) Detectar cambios y calcular deltas crudos
            prev_production = int(inventario.production or 0)
            prev_output     = int(inventario.output or 0)

            new_production = request.data.get('production', None)
            new_output     = request.data.get('output', None)

            if new_production is None:
                new_production = prev_production
            else:
                try:
                    new_production = int(new_production)
                except (TypeError, ValueError):
                    return Response({"message": "'production' debe ser un número."},
                                    status=status.HTTP_400_BAD_REQUEST)

            if new_output is None:
                new_output = prev_output
            else:
                try:
                    new_output = int(new_output)
                except (TypeError, ValueError):
                    return Response({"message": "'output' debe ser un número."},
                                    status=status.HTTP_400_BAD_REQUEST)

            changed_prod = (new_production != prev_production)
            changed_out  = (new_output != prev_output)
            if changed_prod and changed_out:
                return Response({"message": "Solo uno de los campos puede cambiar por solicitud: 'production' o 'output'."},
                                status=status.HTTP_400_BAD_REQUEST)

            # 4) Guardar con serializer (otros campos)
            serializer = serializer_class(inventario, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response({"message": "Error al actualizar el inventario.",
                                "errors": serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)
            inventario = serializer.save()

            # 5) Si no cambió production/output, fin
            if not changed_prod and not changed_out:
                return Response({"message": "Inventario actualizado exitosamente.",
                                "inventario": serializer.data},
                                status=status.HTTP_200_OK)

            # 6) Efecto sobre saldos según qué campo cambió (NO usamos 'categori' aquí)
            if changed_prod:
                delta = new_production - prev_production      # + sube producción, - baja producción
                efecto = delta                                # producción afecta sumando
            else:
                delta = new_output - prev_output              # + sube salida, - baja salida
                efecto = -delta                               # salida afecta restando

            # 7) Actualizar STOCK del Producto (con validación de no-negativo)
            producto = inventario.id_producto
            if inv_type == 1:
                nuevo_stock = int(producto.warehouse_quantity_conforme or 0) + efecto
                if nuevo_stock < 0:
                    return Response(
                        {"message": f"Stock conforme insuficiente para aplicar el cambio (quedaría {nuevo_stock})."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                producto.warehouse_quantity_conforme = nuevo_stock
                producto.save(update_fields=["warehouse_quantity_conforme"])
            else:  # inv_type == 2
                nuevo_stock = int(producto.warehouse_quantity_not_conforme or 0) + efecto
                if nuevo_stock < 0:
                    return Response(
                        {"message": f"Stock no conforme insuficiente para aplicar el cambio (quedaría {nuevo_stock})."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                producto.warehouse_quantity_not_conforme = nuevo_stock
                producto.save(update_fields=["warehouse_quantity_not_conforme"])

            # 8) Aplicar efecto al propio registro y a los posteriores (mismo producto/tipo)
            if efecto != 0:
                # este registro
                inventario.saldo_almacen = (inventario.saldo_almacen or 0) + efecto
                inventario.save(update_fields=["saldo_almacen"])

                filtro = {
                    "id_producto": inventario.id_producto,
                    "inventory_type": inventario.inventory_type,
                }

                posteriores = (Inventario.objects
                            .select_for_update()
                            .filter(**filtro, id__gt=inventario.id)
                            .order_by("id"))

                for inv in posteriores:
                    inv.saldo_almacen = (inv.saldo_almacen or 0) + efecto
                    inv.save(update_fields=["saldo_almacen"])

            return Response({"message": "Inventario actualizado exitosamente.",
                            "inventario": serializer.data},
                            status=status.HTTP_200_OK)