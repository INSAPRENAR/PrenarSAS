from rest_framework.views import APIView
from rest_framework.response import Response
from api_prenar.serializers.userSerializers import UserSerializer
import jwt
from rest_framework.exceptions import AuthenticationFailed
from api_prenar.models.usuario import User

class UsersView(APIView):
    def get(self, request):
        token=request.COOKIES.get('jwt')
        if not token:
           raise AuthenticationFailed('Unauthenticated')
        try:
            payloads=jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated')
        user=User.objects.filter(id=payloads['id']).first()
        serializer=UserSerializer(user)
        return Response(serializer.data)