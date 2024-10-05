import json

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
import redis
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import UserRegistrationSerializer, UserDetailSerializer, CustomTokenObtainPairSerializer

User = get_user_model()
redis_instance = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)


class UserRegistrationView(generics.CreateAPIView):
    """
    post:
    User registration endpoint.

    Allows a new user to register by providing their phone number, first name, last name, and password.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class UserDetailView(generics.RetrieveAPIView):
    """
    get:
    Retrieve authenticated user's details.
    """
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ActivateUserView(APIView):
    """
    post:
    Activate a user account with the activation code sent via SMS.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Activate user account",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['phone_number', 'activation_code'],
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='User phone number'),
                'activation_code': openapi.Schema(type=openapi.TYPE_STRING, description='Activation code sent via SMS'),
            },
        ),
        responses={
            200: openapi.Response('Account activated successfully'),
            400: openapi.Response('Invalid activation code or data'),
        },
    )
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        activation_code = request.data.get('activation_code')

        if not phone_number or not activation_code:
            return Response(
                {'error': 'Phone number and activation code are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        activation_data_json = redis_instance.get(f"activation_data:{phone_number}")
        if activation_data_json:
            activation_data = json.loads(activation_data_json.decode('utf-8'))
            stored_code = activation_data.get('activation_code')
            user_data = activation_data.get('user_data')

            if stored_code == activation_code:
                User.objects.create(**user_data)
                redis_instance.delete(f"activation_data:{phone_number}")
                return Response({'message': 'Account activated successfully.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid activation code.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Activation data not found or expired.'}, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    post:
    Obtain JWT access and refresh tokens by providing phone number and password.
    """
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """
    post:
    Logout user by blacklisting their refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Logout user by blacklisting the refresh token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token to blacklist'),
            },
        ),
        responses={
            205: openapi.Response('Logout successful'),
            400: openapi.Response('Invalid token'),
        },
    )
    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
