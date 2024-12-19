from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.serializers.inventarioSerializers import InventarioSerializer
from api_prenar.models import Inventario

class InventarioView(APIView):
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

        try:
            # Buscar el registro de inventario
            inventario = Inventario.objects.get(id=inventario_id)

            # Verificar si hay un producto relacionado
            producto = inventario.id_producto

            # Ajustar warehouse_quantity dependiendo de producción o salida
            if inventario.total_production > 0:
                producto.warehouse_quantity -= inventario.total_production
            elif inventario.total_output > 0:
                producto.warehouse_quantity += inventario.total_output

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