import json

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
import random
import redis
from django.conf import settings

from config.utils import get_sms_client
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()
redis_instance = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('phone_number', 'first_name', 'last_name', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': "Password fields didn't match."})
        return attrs

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def create(self, validated_data):
        validated_data.pop('password2')
        # activation_code = f"{random.randint(100000, 999999)}"
        activation_code = "123456"
        phone_number = validated_data['phone_number']
        user_data = validated_data

        activation_data = {
            'activation_code': activation_code,
            'user_data': user_data
        }

        redis_instance.set(
            name=f"activation_data:{phone_number}",
            value=json.dumps(activation_data),
            ex=settings.ACTIVATION_CODE_EXPIRY
        )

        sms_client = get_sms_client()
        success, message = sms_client.send_sms(phone_number, f"Код верификации для входа: {activation_code}")
        return user_data


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'phone_number', 'first_name', 'last_name', 'role')


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'phone_number'

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')

        if phone_number and password:
            user = authenticate(request=self.context.get('request'), phone_number=phone_number, password=password)

            if not user:
                raise serializers.ValidationError('Invalid credentials.', code='authorization')

            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.', code='authorization')

            refresh = self.get_token(user)

            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        else:
            raise serializers.ValidationError('Must include "phone_number" and "password".', code='authorization')
