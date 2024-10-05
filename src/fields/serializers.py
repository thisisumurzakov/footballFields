from rest_framework import serializers
from django.utils import timezone
from datetime import datetime

from location.models import District
from location.serializers import DistrictSerializer

from .models import FootballField, Booking, FieldImage


class FieldImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldImage
        fields = ['id', 'image']


class FootballFieldSerializer(serializers.ModelSerializer):
    images = FieldImageSerializer(many=True, read_only=True)
    owner = serializers.CharField(source='owner.phone_number', read_only=True)
    district = DistrictSerializer(read_only=True)
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(), source='district', write_only=True
    )

    class Meta:
        model = FootballField
        fields = [
            'id', 'owner', 'name', 'address', 'district', 'district_id', 'contact',
            'hourly_rate', 'description', 'opening_time', 'closing_time',
            'min_booking_duration', 'latitude', 'longitude', 'images', 'created_at'
        ]
        read_only_fields = ['owner', 'created_at']

    def create(self, validated_data):
        images_data = self.context['request'].FILES.getlist('images')
        field = FootballField.objects.create(**validated_data)
        for image_data in images_data:
            FieldImage.objects.create(field=field, image=image_data)
        return field

    def update(self, instance, validated_data):
        images_data = self.context['request'].FILES.getlist('images')

        # Update field instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Optionally update images
        if images_data:
            instance.images.all().delete()
            for image_data in images_data:
                FieldImage.objects.create(field=instance, image=image_data)

        return instance


class BookingSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.phone_number', read_only=True)
    field_name = serializers.CharField(source='field.name', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'field', 'field_name', 'user', 'start_time', 'end_time', 'created_at']
        read_only_fields = ['user', 'created_at']

    def validate(self, data):
        start_time = data['start_time']
        end_time = data['end_time']
        field = data['field']

        if start_time <= timezone.now():
            raise serializers.ValidationError('Start time must be in the future.')

        if end_time <= start_time:
            raise serializers.ValidationError('End time must be after start time.')

        booking_duration = end_time - start_time

        if booking_duration < field.min_booking_duration:
            min_duration_minutes = int(field.min_booking_duration.total_seconds() // 60)
            raise serializers.ValidationError(f'Booking duration must be at least {min_duration_minutes} minutes.')

        booking_duration_seconds = booking_duration.total_seconds()
        min_duration_seconds = field.min_booking_duration.total_seconds()

        if booking_duration_seconds % min_duration_seconds != 0:
            min_duration_minutes = int(min_duration_seconds // 60)
            raise serializers.ValidationError(f'Booking duration must be a multiple of the minimum booking duration ({min_duration_minutes} minutes).')

        # Ensure booking times are within the field's working hours
        field_opening_datetime = timezone.make_aware(datetime.combine(start_time.date(), field.opening_time))
        field_closing_datetime = timezone.make_aware(datetime.combine(start_time.date(), field.closing_time))

        if not (field_opening_datetime <= start_time < field_closing_datetime) or not (field_opening_datetime < end_time <= field_closing_datetime):
            raise serializers.ValidationError('Booking times must be within the field\'s working hours.')

        # Check for overlapping bookings
        overlapping_bookings = Booking.objects.filter(
            field=field,
            start_time__lt=end_time,
            end_time__gt=start_time
        )

        if overlapping_bookings.exists():
            raise serializers.ValidationError('This field is already booked for the given time.')

        return data
