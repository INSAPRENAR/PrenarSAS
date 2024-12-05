from rest_framework.views import APIView
from rest_framework.response import Response
import jwt

class LogoutView(APIView):
    def post(self, request):
        response=Response()
        response.delete_cookie('jwt')
        response.data={
            'message':'succes'
        }
        return response