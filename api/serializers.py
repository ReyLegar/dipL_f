from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from api.models import CreditApplication


class CustomTokenObtainPairSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')
        user = authenticate(phone_number=phone_number, password=password)
        if not user:
            raise serializers.ValidationError('Invalid login credentials')
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled')
        refresh = RefreshToken.for_user(user)
        return {'access': str(refresh.access_token), 'refresh': str(refresh)}

class CreditApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditApplication
        fields = ['amount', 'status']