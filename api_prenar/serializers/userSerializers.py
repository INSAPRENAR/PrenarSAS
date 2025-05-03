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
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['name', 'email', 'role', 'password']
        extra_kwargs = {
            'email': {'required': False},
            'name': {'required': False},
            'role': {'required': False},
        }

    def update(self, instance, validated_data):
        # 1) Si envían password, la extraemos para usar set_password más abajo
        pwd = validated_data.pop('password', None)

        # 2) Actualizamos solo los demás campos (name, email, role)
        instance = super().update(instance, validated_data)

        # 3) Si había password, la seteamos con el método correcto
        if pwd:
            instance.set_password(pwd)
            instance.save()

        return instance

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'role']

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','name','email','role']
        extra_kwargs = {
            'password': {'write_only': True} 
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Convierte el campo `role` al valor de visualización
        representation['role'] = instance.get_role_display()
        return representation