from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import Producto
from api_prenar.serializers.productoSerializers import ProductoSerializer
from rest_framework.pagination import PageNumberPagination

class ProductoView(APIView):
    def post(self, request):
        """
        Crea un nuevo producto.
        """
        serializer = ProductoSerializer(data=request.data)
        if serializer.is_valid():
            try:
                producto = serializer.save()
                return Response(
                    {
                        "message": "Producto registrado exitosamente.",
                        "data": serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {
                        "message": "Error al registrar el producto.",
                        "error": str(e)
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(
            {
                "message": "Error en la validación de los datos.",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    

    def get(self, request):
        try:
            # Obtener todos los productos ordenados por '-id' (opcional)
            productos = Producto.objects.all().order_by('-id')

            if not productos.exists():
                return Response([], status=status.HTTP_200_OK)  # Devolver array vacío si no hay productos

            # Inicializar el paginador
            paginator = PageNumberPagination()
            paginator.page_size = 20  # Define el número de productos por página (ajusta según tus necesidades)
            paginated_productos = paginator.paginate_queryset(productos, request)

            # Serializar los productos paginados
            serializer = ProductoSerializer(paginated_productos, many=True)

            # Retornar la respuesta paginada
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {"message": "Error al obtener los productos.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def put(self, request, producto_id):
        """
        Actualiza un producto existente.
        """
        try:
            # Obtener el producto por su ID
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return Response(
                {"message": f"No se encontró el producto con ID {id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Serializar los datos enviados para actualización
        serializer = ProductoSerializer(producto, data=request.data, partial=False)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Producto actualizado exitosamente.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {"message": "Error al actualizar el producto.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request, producto_id):
        try:
            # Intentar obtener el producto por su ID
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return Response(
                {"message": f"No se encontró el producto con ID {id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Eliminar el producto
        producto.delete()
        return Response(
            {"message": f"Producto con ID {id} eliminado exitosamente."},
            status=status.HTTP_200_OK
        )