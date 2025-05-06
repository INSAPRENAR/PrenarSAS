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
        try:
            inventario = Inventario.objects.get(id=inventario_id)
        except Inventario.DoesNotExist:
            return Response(
                {"message": "Inventario no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. Determinar qué serializador usar
        #    Asegúrate de que inventory_type esté en el body
        inventory_type = request.data.get('inventory_type', None)
        if inventory_type is None:
            return Response(
                {"message": "Debe enviar 'inventory_type' en el payload."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convertimos a entero para la comparación
        try:
            inv_type = int(inventory_type)
        except (TypeError, ValueError):
            return Response(
                {"message": "'inventory_type' debe ser un número."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Selección dinámica del serializador
        if inv_type == 1:
            serializer_class = InventarioSerializerInventario
        elif inv_type == 2:
            serializer_class = InventarioSerializerInventarioDos
        else:
            return Response(
                {"message": "Valor de 'inventory_type' inválido. Debe ser 1 o 2."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Instanciar y validar
        serializer = serializer_class(inventario, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Inventario actualizado exitosamente.",
                    "inventario": serializer.data
                },
                status=status.HTTP_200_OK
            )

        # 5. Responder con errores
        return Response(
            {
                "message": "Error al actualizar el inventario.",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )