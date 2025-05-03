from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from api_prenar.models.usuario import User
from api_prenar.serializers.userSerializers import UserUpdateSerializer

class UserDetail(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, user_id):
        """
        Reemplaza (PUT) todos los campos indicados en el serializer.
        """
        if not request.user.is_superuser:
            raise PermissionDenied("No tienes permisos para realizar esta acción.")
        
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise NotFound("Usuario no encontrado.")
        
        # Para PUT, normalmente esperamos un reemplazo completo,
        # así que omitimos partial o lo ponemos en False.
        serializer = UserUpdateSerializer(user, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Usuario actualizado exitosamente.", "Usuario": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, user_id):
        """
        Elimina un usuario por su ID.
        """
        if not request.user.is_superuser:
            raise PermissionDenied("No tienes permisos para realizar esta acción.")

        user = User.objects.filter(id=user_id).first()
        if not user:
            raise NotFound("Usuario no encontrado.")
        
        # Eliminar el usuario
        user.delete()
        
        # Respuesta de éxito
        return Response({"message": "Usuario eliminado correctamente."}, status=status.HTTP_200_OK)