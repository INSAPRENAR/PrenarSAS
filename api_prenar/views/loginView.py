from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
import jwt, datetime
from api_prenar.models.usuario import User

class loginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = User.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed('Usuario No existe!')
        
        if not user.check_password(password):
            raise AuthenticationFailed('Contraseña Incorrecta!')
        
        # Generar el RefreshToken y AccessToken con SimpleJWT
        refresh = RefreshToken.for_user(user)

        # Enviar los tokens en la respuesta
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })