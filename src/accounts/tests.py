from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
import redis
from django.conf import settings
import json

User = get_user_model()
redis_instance = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)


class UserRegistrationTests(APITestCase):
    @patch('accounts.serializers.get_sms_client')
    def test_user_registration(self, mock_get_sms_client):
        # Set up the mock SMS client
        mock_sms_client = mock_get_sms_client.return_value
        mock_sms_client.send_sms.return_value = (True, "SMS sent successfully")

        url = reverse('register')
        data = {
            'phone_number': '+14155552671',  # Updated to a valid phone number
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'TestPassword123',
            'password2': 'TestPassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that activation data is stored in Redis
        activation_data = redis_instance.get(f"activation_data:{data['phone_number']}")
        self.assertIsNotNone(activation_data)

        # Assert that SMS was sent
        mock_sms_client.send_sms.assert_called_once_with(
            '+14155552671',
            'Код верификации для входа: 123456'
        )

    @patch('accounts.serializers.get_sms_client')
    def test_user_registration_password_mismatch(self, mock_get_sms_client):
        mock_sms_client = mock_get_sms_client.return_value

        url = reverse('register')
        data = {
            'phone_number': '+14155552672',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'password': 'TestPassword123',
            'password2': 'DifferentPassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

        mock_sms_client.send_sms.assert_not_called()

    @patch('accounts.serializers.get_sms_client')
    def test_user_registration_duplicate_phone_number(self, mock_get_sms_client):
        mock_sms_client = mock_get_sms_client.return_value

        # First registration
        User.objects.create_user(
            phone_number='+14155552671',
            first_name='Existing',
            last_name='User',
            password='ExistingPassword'
        )
        url = reverse('register')
        data = {
            'phone_number': '+14155552671',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'TestPassword123',
            'password2': 'TestPassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)

        mock_sms_client.send_sms.assert_not_called()


class UserActivationTests(APITestCase):
    def setUp(self):
        # Simulate registration
        self.phone_number = '+1234567890'
        self.user_data = {
            'phone_number': self.phone_number,
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'TestPassword123'
        }
        activation_data = {
            'activation_code': '123456',
            'user_data': self.user_data
        }
        activation_data_json = json.dumps(activation_data)
        redis_instance.set(
            name=f"activation_data:{self.phone_number}",
            value=activation_data_json,
            ex=settings.ACTIVATION_CODE_EXPIRY
        )

    def test_user_activation(self):
        url = reverse('activate')
        data = {
            'phone_number': self.phone_number,
            'activation_code': '123456'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Account activated successfully.')

        # Check that the user now exists in the database
        user_exists = User.objects.filter(phone_number=self.phone_number).exists()
        self.assertTrue(user_exists)

        # Check that activation data is removed from Redis
        activation_data = redis_instance.get(f"activation_data:{self.phone_number}")
        self.assertIsNone(activation_data)

    def test_user_activation_invalid_code(self):
        url = reverse('activate')
        data = {
            'phone_number': self.phone_number,
            'activation_code': '000000'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Invalid activation code.')

        # User should not be created
        user_exists = User.objects.filter(phone_number=self.phone_number).exists()
        self.assertFalse(user_exists)


class UserLoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number='+1234567890',
            first_name='John',
            last_name='Doe',
            password='TestPassword123'
        )

    def test_user_login(self):
        url = reverse('token_obtain_pair')
        data = {
            'phone_number': '+1234567890',
            'password': 'TestPassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_login_invalid_credentials(self):
        url = reverse('token_obtain_pair')
        data = {
            'phone_number': '+998000000000',
            'password': 'WrongPassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)


class UserDetailTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number='+1234567890',
            first_name='John',
            last_name='Doe',
            password='TestPassword123'
        )
        self.url = reverse('user_detail')

    def test_get_user_details(self):
        # Authenticate the user
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], str(self.user.phone_number))
        self.assertEqual(response.data['first_name'], self.user.first_name)
        self.assertEqual(response.data['last_name'], self.user.last_name)
        self.assertEqual(response.data['role'], self.user.role)


class UserLogoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number='+1234567890',
            first_name='John',
            last_name='Doe',
            password='TestPassword123'
        )
        self.url = reverse('logout')
        # Obtain tokens
        token_url = reverse('token_obtain_pair')
        data = {
            'phone_number': '+1234567890',
            'password': 'TestPassword123'
        }
        response = self.client.post(token_url, data, format='json')
        self.access_token = response.data['access']
        self.refresh_token = response.data['refresh']

    def test_user_logout(self):
        # Authenticate the user
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        data = {'refresh': self.refresh_token}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_user_logout_invalid_token(self):
        # Authenticate the user
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        data = {'refresh': 'invalid_refresh_token'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
