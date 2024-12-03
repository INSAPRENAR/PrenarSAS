from rest_framework import serializers
from api_prenar.models.usuario import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        field = ['id','name','email','password']
        extra_kwargs = {
            'password': {'write_only':True}
        }