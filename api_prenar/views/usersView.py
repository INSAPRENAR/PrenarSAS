from rest_framework.views import APIView
from rest_framework.response import Response
from api_prenar.serializers.userSerializers import UserSerializer
import jwt
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated

class UsersView(APIView):
    # Añadimos permiso para asegurar que el usuario está autenticado
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Obtenemos el token desde la cabecera Authorization
        token = request.headers.get('Authorization')

        # Verificamos si el token está presente en la cabecera
        if not token:
            raise AuthenticationFailed('Token no proporcionado.')

        # Asegúrate de que el token tiene el prefijo "Bearer "
        if not token.startswith('Bearer '):
            raise AuthenticationFailed('Token mal formado.')

        token = token[7:]  # Eliminamos "Bearer " del token

        # Usamos JWTAuthentication para verificar el token
        try:
            # Usamos la autenticación de JWT de rest_framework_simplejwt
            jwt_authentication = JWTAuthentication()
            user, _ = jwt_authentication.authenticate(request)
        except AuthenticationFailed:
            raise AuthenticationFailed('Token inválido o expirado.')

        # Si el usuario está autenticado, procedemos a devolver los datos del usuario
        serializer = UserSerializer(user)
        return Response(serializer.data)