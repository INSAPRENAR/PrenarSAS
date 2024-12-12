from rest_framework import serializers
from api_prenar.models.usuario import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','name','email','password','role']
        extra_kwargs = {
            'password': {'write_only':True}
        }
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'role']

    def update(self, instance, validated_data):
        #Si la contraseña es parte de los datos, la encriptamos antes de guardarla
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])  #Encripta la contraseña
            validated_data['password'] = instance.password  #Aseguramos que la contraseña encriptada esté en validated_data
        
        #Guardamos el resto de los datos (email y role)
        return super().update(instance, validated_data)

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'role']