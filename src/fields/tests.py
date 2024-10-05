from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, time
from location.models import Region, City, District
from .models import FootballField, Booking

User = get_user_model()


class FieldsAppTests(APITestCase):
    def setUp(self):
        # Create a regular user
        self.user = User.objects.create_user(
            phone_number='+14155552671',
            first_name='Regular',
            last_name='User',
            password='UserPassword123',
            role='user'
        )
        # Create an owner
        self.owner = User.objects.create_user(
            phone_number='+14155552672',
            first_name='Field',
            last_name='Owner',
            password='OwnerPassword123',
            role='owner'
        )
        # Create an admin
        self.admin = User.objects.create_user(
            phone_number='+14155552673',
            first_name='Admin',
            last_name='User',
            password='AdminPassword123',
            role='admin'
        )

        # Create a region, city, and district
        self.region = Region.objects.create(name='Test Region')
        self.city = City.objects.create(name='Test City', region=self.region)
        self.district = District.objects.create(name='Test District', city=self.city)

        # Create two football fields owned by the owner
        self.field = FootballField.objects.create(
            owner=self.owner,
            name='Test Field',
            address='123 Soccer St.',
            district=self.district,
            contact='owner@example.com',
            hourly_rate='50.00',
            opening_time=time(8, 0),
            closing_time=time(22, 0),
            min_booking_duration=timedelta(hours=1),
            latitude=40.7128,
            longitude=-74.0060
        )

    def test_owner_can_create_field(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('field-list')
        data = {
            'name': 'New Field',
            'address': '456 Football Ave.',
            'district_id': self.district.id,
            'contact': 'owner2@example.com',
            'hourly_rate': '60.00',
            'opening_time': '09:00',
            'closing_time': '21:00',
            'min_booking_duration': '01:00:00',
            'latitude': 40.730610,
            'longitude': -73.935242
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FootballField.objects.count(), 2)
        self.assertEqual(FootballField.objects.latest('id').name, 'New Field')

    def test_user_cannot_create_field(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('field-list')
        data = {
            'name': 'Unauthorized Field',
            'address': '789 Unauthorized Rd.',
            'contact': 'user@example.com',
            'hourly_rate': '40.00',
            'opening_time': '10:00',
            'closing_time': '20:00',
            'min_booking_duration': '01:00:00',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_field_retrieval(self):
        url = reverse('field-detail', kwargs={'pk': self.field.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.field.name)

    def test_owner_can_update_field(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('field-detail', kwargs={'pk': self.field.id})
        data = {
            'name': 'Updated Field Name',
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.field.refresh_from_db()
        self.assertEqual(self.field.name, 'Updated Field Name')

    def test_user_cannot_update_field(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('field-detail', kwargs={'pk': self.field.id})
        data = {
            'name': 'Malicious Update',
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.field.refresh_from_db()
        self.assertNotEqual(self.field.name, 'Malicious Update')

    def test_owner_can_delete_field(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('field-detail', kwargs={'pk': self.field.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FootballField.objects.filter(id=self.field.id).exists())

    def test_user_cannot_delete_field(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('field-detail', kwargs={'pk': self.field.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(FootballField.objects.filter(id=self.field.id).exists())

    def test_user_can_create_booking(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('booking-list')
        start_time = (timezone.now() + timedelta(hours=2)).replace(microsecond=0, second=0, minute=0)
        end_time = start_time + timedelta(hours=2)  # Booking for 2 hours
        data = {
            'field': self.field.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.user, self.user)

    def test_booking_with_past_start_time(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('booking-list')
        start_time = (timezone.now() - timedelta(hours=1)).replace(microsecond=0, second=0, minute=0)
        end_time = (timezone.now() + timedelta(hours=1)).replace(microsecond=0, second=0, minute=0)
        data = {
            'field': self.field.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertIn('Start time must be in the future.', response.data['non_field_errors'][0])

    def test_booking_duration_not_multiple_of_min_duration(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('booking-list')
        start_time = (timezone.now() + timedelta(hours=3)).replace(microsecond=0, second=0, minute=0)
        end_time = start_time + timedelta(minutes=90)  # 1.5 hours
        data = {
            'field': self.field.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertIn('Booking duration must be a multiple of the minimum booking duration', response.data['non_field_errors'][0])

    def test_booking_outside_working_hours(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('booking-list')
        # Booking before opening time
        start_time = (timezone.now() + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        data = {
            'field': self.field.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertIn('Booking times must be within the field\'s working hours.', response.data['non_field_errors'][0])

    def test_booking_overlapping(self):
        # Create an existing booking with precise times
        existing_start_time = (timezone.now() + timedelta(hours=4)).replace(microsecond=0, second=0, minute=0)
        existing_end_time = existing_start_time + timedelta(hours=2)  # Booking from 4 PM to 6 PM
        existing_booking = Booking.objects.create(
            field=self.field,
            user=self.user,
            start_time=existing_start_time,
            end_time=existing_end_time
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('booking-list')
        # New booking overlapping with existing booking
        new_start_time = existing_start_time + timedelta(hours=1)  # 5 PM
        new_end_time = new_start_time + timedelta(hours=2)  # 5 PM to 7 PM
        data = {
            'field': self.field.id,
            'start_time': new_start_time.isoformat(),
            'end_time': new_end_time.isoformat(),
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertIn('This field is already booked for the given time.', response.data['non_field_errors'][0])

    def test_user_can_retrieve_own_bookings(self):
        booking_start_time = (timezone.now() + timedelta(hours=3)).replace(microsecond=0, second=0, minute=0)
        booking_end_time = booking_start_time + timedelta(hours=2)
        booking = Booking.objects.create(
            field=self.field,
            user=self.user,
            start_time=booking_start_time,
            end_time=booking_end_time
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('booking-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_owner_can_retrieve_bookings_for_their_fields(self):
        booking_start_time = (timezone.now() + timedelta(hours=3)).replace(microsecond=0, second=0, minute=0)
        booking_end_time = booking_start_time + timedelta(hours=2)
        booking = Booking.objects.create(
            field=self.field,
            user=self.user,
            start_time=booking_start_time,
            end_time=booking_end_time
        )
        self.client.force_authenticate(user=self.owner)
        url = reverse('booking-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_user_cannot_delete_others_booking(self):
        other_user = User.objects.create_user(
            phone_number='+14155552674',
            first_name='Other',
            last_name='User',
            password='OtherPassword123',
            role='user'
        )
        booking_start_time = (timezone.now() + timedelta(hours=4)).replace(microsecond=0, second=0, minute=0)
        booking_end_time = booking_start_time + timedelta(hours=2)
        booking = Booking.objects.create(
            field=self.field,
            user=other_user,
            start_time=booking_start_time,
            end_time=booking_end_time
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('booking-detail', kwargs={'pk': booking.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Booking.objects.filter(id=booking.id).exists())

    def test_user_can_delete_own_booking(self):
        booking_start_time = (timezone.now() + timedelta(hours=3)).replace(microsecond=0, second=0, minute=0)
        booking_end_time = booking_start_time + timedelta(hours=2)
        booking = Booking.objects.create(
            field=self.field,
            user=self.user,
            start_time=booking_start_time,
            end_time=booking_end_time
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('booking-detail', kwargs={'pk': booking.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Booking.objects.filter(id=booking.id).exists())

    def test_get_available_fields(self):
        # Create another field
        another_field = FootballField.objects.create(
            owner=self.owner,
            name='Another Field',
            address='789 Soccer Rd.',
            district=self.district,  # Provide the district
            contact='owner@example.com',
            hourly_rate='55.00',
            opening_time=time(8, 0),
            closing_time=time(22, 0),
            min_booking_duration=timedelta(hours=1),
            latitude=40.730610,
            longitude=-73.935242
        )
        # Create a booking on the first field
        booking_start_time = (timezone.now() + timedelta(hours=4)).replace(microsecond=0, second=0, minute=0)
        booking_end_time = booking_start_time + timedelta(hours=2)  # Booking from 4 PM to 6 PM
        Booking.objects.create(
            field=self.field,
            user=self.user,
            start_time=booking_start_time,
            end_time=booking_end_time
        )
        url = reverse('available-fields')
        # Request available fields for the same time as the booking
        response = self.client.get(url, {
            'start_time': booking_start_time.isoformat(),
            'end_time': booking_end_time.isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only the second field should be available
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Another Field')

    def test_get_available_fields_sorted_by_distance(self):
        """
        Test that fields are returned sorted by distance to the given latitude and longitude.
        """
        field_2 = FootballField.objects.create(
            owner=self.owner,
            name='Test Field 2',
            address='456 Soccer Ave.',
            district=self.district,
            contact='owner2@example.com',
            hourly_rate='60.00',
            opening_time=time(8, 0),
            closing_time=time(22, 0),
            min_booking_duration=timedelta(hours=1),
            latitude=34.0522,  # Los Angeles
            longitude=-118.2437
        )
        url = reverse('available-fields')
        # Query for fields near New York (lat: 40.7128, lon: -74.0060)
        response = self.client.get(url, {
            'latitude': 40.730610,
            'longitude': -73.935242,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that fields are returned in order of proximity
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Test Field')  # Closest to New York
        self.assertEqual(response.data[1]['name'], 'Test Field 2')  # Farther in Los Angeles

    def test_get_available_fields_within_time_range(self):
        """
        Test that only available fields within the given time range are returned.
        """
        # Create a booking on Field 1
        booking_start_time = (timezone.now() + timedelta(hours=4)).replace(microsecond=0, second=0, minute=0)
        booking_end_time = booking_start_time + timedelta(hours=2)  # Booking from 4 PM to 6 PM
        Booking.objects.create(
            field=self.field,
            user=self.user,
            start_time=booking_start_time,
            end_time=booking_end_time
        )
        FootballField.objects.create(
            owner=self.owner,
            name='Test Field 2',
            address='456 Soccer Ave.',
            district=self.district,
            contact='owner2@example.com',
            hourly_rate='60.00',
            opening_time=time(8, 0),
            closing_time=time(22, 0),
            min_booking_duration=timedelta(hours=1),
            latitude=34.0522,
            longitude=-118.2437
        )

        url = reverse('available-fields')
        # Query for available fields for the same time range as the booking
        response = self.client.get(url, {
            'start_time': booking_start_time.isoformat(),
            'end_time': booking_end_time.isoformat(),
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only Field 2 should be available as Field 1 is booked
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Field 2')

    def test_get_available_fields_near_given_location(self):
        """
        Test that fields near a specific latitude and longitude are retrieved and sorted by distance.
        """
        # Create a second field farther away
        FootballField.objects.create(
            owner=self.owner,
            name='Test Field 2',
            address='456 Soccer Ave.',
            district=self.district,
            contact='owner2@example.com',
            hourly_rate='60.00',
            opening_time=time(8, 0),
            closing_time=time(22, 0),
            min_booking_duration=timedelta(hours=1),
            latitude=34.0522,
            longitude=-118.2437
        )

        url = reverse('available-fields')

        # Query for fields near New York (latitude: 40.730610, longitude: -73.935242)
        response = self.client.get(url, {
            'latitude': 40.730610,
            'longitude': -73.935242,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that fields are returned and sorted by proximity
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Test Field')
        self.assertEqual(response.data[1]['name'], 'Test Field 2')

