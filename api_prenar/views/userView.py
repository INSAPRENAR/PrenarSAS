from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, PermissionDenied
from api_prenar.models.usuario import User
from api_prenar.serializers.userSerializers import UserDetailSerializer

class UserView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, user_id):
        if not request.user.is_superuser:
            raise PermissionDenied("No tienes permisos para acceder a esta información.")
        
        # Intentamos obtener el usuario con el ID proporcionado
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFound("Usuario no encontrado.")

        # Serializamos los datos del usuario
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)