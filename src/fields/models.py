from _decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime

from location.models import District


class FootballField(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='fields', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    district = models.ForeignKey(District, related_name='fields', on_delete=models.PROTECT)
    contact = models.CharField(max_length=100)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    min_booking_duration = models.DurationField(default=timezone.timedelta(hours=1))
    created_at = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('-90.0')), MaxValueValidator(Decimal('90.0'))],
        null=False,
        blank=False
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('-180.0')), MaxValueValidator(Decimal('180.0'))],
        null=False,
        blank=False
    )

    def __str__(self):
        return self.name


class FieldImage(models.Model):
    field = models.ForeignKey(
        FootballField,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='field_images/')

    def __str__(self):
        return f"Image for {self.field.name}"


class Booking(models.Model):
    field = models.ForeignKey(
        FootballField,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.field.name} booked by {self.user.phone_number}"

    class Meta:
        unique_together = ('field', 'start_time', 'end_time')

    def clean(self):
        if self.start_time <= timezone.now():
            raise ValidationError('Start time must be in the future.')

        if self.end_time <= self.start_time:
            raise ValidationError('End time must be after start time.')

        booking_duration = self.end_time - self.start_time

        # Check that booking duration is at least the minimum booking duration
        if booking_duration < self.field.min_booking_duration:
            min_duration_minutes = int(self.field.min_booking_duration.total_seconds() // 60)
            raise ValidationError(f'Booking duration must be at least {min_duration_minutes} minutes.')

        # Check that booking duration is a multiple of min_booking_duration
        booking_duration_seconds = int(booking_duration.total_seconds())
        min_duration_seconds = int(self.field.min_booking_duration.total_seconds())

        if booking_duration_seconds % min_duration_seconds != 0:
            min_duration_minutes = int(min_duration_seconds // 60)
            raise ValidationError(
                f'Booking duration must be a multiple of the minimum booking duration ({min_duration_minutes} minutes).'
            )

        # Ensure booking times are within the field's working hours
        field_opening_datetime = timezone.make_aware(datetime.combine(self.start_time.date(), self.field.opening_time))
        field_closing_datetime = timezone.make_aware(datetime.combine(self.start_time.date(), self.field.closing_time))

        if not (field_opening_datetime <= self.start_time < field_closing_datetime) or not (field_opening_datetime < self.end_time <= field_closing_datetime):
            raise ValidationError('Booking times must be within the field\'s working hours.')

        # Check for overlapping bookings
        overlapping_bookings = Booking.objects.filter(
            field=self.field,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(pk=self.pk)

        if overlapping_bookings.exists():
            raise ValidationError('This field is already booked for the given time.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
