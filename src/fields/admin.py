from django.contrib import admin

from .models import Booking, FieldImage, FootballField


class FieldImageInline(admin.TabularInline):
    model = FieldImage
    extra = 1


@admin.register(FootballField)
class FootballFieldAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "owner", "district", "hourly_rate"]
    list_filter = ["owner", "district"]
    search_fields = ["name", "address"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["field", "user", "start_time", "end_time", "created_at"]
    list_filter = ["field", "start_time"]
