from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Region, City, District

User = get_user_model()


class LocationTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            phone_number='+14155552670',
            first_name='Admin',
            last_name='User',
            password='AdminPassword123'
        )
        self.regular_user = User.objects.create_user(
            phone_number='+14155552671',
            first_name='Regular',
            last_name='User',
            password='UserPassword123'
        )
        self.region = Region.objects.create(name='Test Region')
        self.city = City.objects.create(name='Test City', region=self.region)
        self.district = District.objects.create(name='Test District', city=self.city)

    def test_admin_can_create_region(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('region-list')
        data = {'name': 'New Region'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Region.objects.count(), 2)

    def test_regular_user_cannot_create_region(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('region-list')
        data = {'name': 'Unauthorized Region'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Region.objects.count(), 1)

    def test_anonymous_user_can_read_regions(self):
        self.client.logout()  # Ensure the user is anonymous
        url = reverse('region-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_anonymous_user_cannot_create_region(self):
        self.client.logout()
        url = reverse('region-list')
        data = {'name': 'Anonymous Region'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Region.objects.count(), 1)

    # Similar tests for City and District

    def test_admin_can_update_region(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('region-detail', kwargs={'pk': self.region.id})
        data = {'name': 'Updated Region'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.region.refresh_from_db()
        self.assertEqual(self.region.name, 'Updated Region')

    def test_regular_user_cannot_update_region(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('region-detail', kwargs={'pk': self.region.id})
        data = {'name': 'Unauthorized Update'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.region.refresh_from_db()
        self.assertNotEqual(self.region.name, 'Unauthorized Update')

    def test_regular_user_can_read_region_detail(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('region-detail', kwargs={'pk': self.region.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.region.name)
