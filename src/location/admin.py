from django.contrib import admin
from .models import Region, City, District


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'region']
    list_filter = ['region']
    search_fields = ['name']


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'city']
    list_filter = ['city']
    search_fields = ['name']
