from rest_framework import serializers

from .models import City, District, Region


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id", "name"]


class CitySerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    region_id = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(), source="region", write_only=True
    )

    class Meta:
        model = City
        fields = ["id", "name", "region", "region_id"]


class DistrictSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(), source="city", write_only=True
    )

    class Meta:
        model = District
        fields = ["id", "name", "city", "city_id"]
