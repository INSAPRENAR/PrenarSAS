from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_prenar.models import GeneracionPassword
from api_prenar.serializers.generacionPasswordSerializers import GeneracionPasswordSerializer

class GeneracionPasswordView(APIView):
    def post(self, request):
        # Verifica si ya existe un registro
        if GeneracionPassword.objects.exists():
            return Response(
                {"message": "Ya existe un registro de generación de contraseña. No se pueden crear más."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = GeneracionPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Guarda la nueva generación de contraseña
            return Response(
                {"message": "Generación de contraseña creada exitosamente."},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"message": "Error al crear la generación de contraseña.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request):
        generacion = GeneracionPassword.objects.all()
        serializer = GeneracionPasswordSerializer(generacion, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, generacion_id):
        try:
            generacion = GeneracionPassword.objects.get(id=generacion_id)
        except GeneracionPassword.DoesNotExist:
            return Response(
                {"message": "Generación de contraseña no encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GeneracionPasswordSerializer(generacion, data=request.data)
        if serializer.is_valid():
            serializer.save()  # Actualiza la generación de contraseña
            return Response(
                {"message": "Generación de contraseña actualizada exitosamente.", "generacion": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(
            {"message": "Error al actualizar la generación de contraseña.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, id):
        try:
            generacion = GeneracionPassword.objects.get(id=id)
        except GeneracionPassword.DoesNotExist:
            return Response(
                {"message": "Generación de contraseña no encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )

        generacion.delete()  # Elimina la generación de contraseña
        return Response(
            {"message": "Generación de contraseña eliminada exitosamente."},
            status=status.HTTP_200_OK
        )