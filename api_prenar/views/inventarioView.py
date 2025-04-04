from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.serializers.inventarioSerializers import InventarioSerializer
from api_prenar.models import Inventario, GeneracionPassword
from django.db import transaction

class InventarioView(APIView):

    def get(self, request):
        try:
            print("Ejecutando método GET")
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
            print(f"Resultado agrupado: {resultado}")

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

            # Verificar si hay un producto y pedido relacionados
            producto = inventario.id_producto
            pedido = inventario.id_pedido

            if not producto or not pedido:
                return Response(
                    {"message": "El inventario no está relacionado con un producto o pedido válido."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                # Ajustar warehouse_quantity dependiendo de producción o salida
                if inventario.total_production > 0:
                    producto.warehouse_quantity -= inventario.total_production
                elif inventario.total_output > 0:
                    producto.warehouse_quantity += inventario.total_output

                # Validar que warehouse_quantity no sea negativa
                if producto.warehouse_quantity < 0:
                    return Response(
                        {"message": f"La cantidad en almacén del producto {producto.name} no puede ser negativa."},
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