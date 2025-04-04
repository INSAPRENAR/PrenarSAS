from rest_framework import serializers
from api_prenar.models import GeneracionPassword

class GeneracionPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneracionPassword
        fields = '__all__'