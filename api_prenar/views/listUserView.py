from rest_framework.views import APIView
from rest_framework.response import Response
from api_prenar.models.usuario import User
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import AuthenticationFailed
import jwt
from api_prenar.serializers.userSerializers import UserDetailSerializer

class ListUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Verificamos que el usuario autenticado sea un superusuario
        if not request.user.is_superuser:
            raise PermissionDenied("No tienes permisos para acceder a esta lista de usuarios.")
        
        # Si el usuario es superusuario, obtenemos solo los usuarios que no son superusuarios
        users = User.objects.filter(is_superuser=False)
        serializer = UserDetailSerializer(users, many=True)
        
        return Response(serializer.data)