from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets

from .models import City, District, Region
from .permissions import IsAdminOrReadOnly
from .serializers import CitySerializer, DistrictSerializer, RegionSerializer


class RegionViewSet(viewsets.ModelViewSet):
    """
    get:
    List all regions or retrieve a specific region by its ID.

    post:
    Create a new region. Only admins can perform this action.

    put:
    Update a region. Only admins can perform this action.

    delete:
    Delete a region. Only admins can perform this action.
    """

    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [IsAdminOrReadOnly]

    @swagger_auto_schema(
        operation_description="Retrieve the list of all regions",
        responses={200: RegionSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new region",
        responses={201: RegionSerializer, 400: "Invalid input", 403: "Forbidden"},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve a specific region by its ID",
        responses={200: RegionSerializer, 404: "Not Found"},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a region",
        responses={200: RegionSerializer, 400: "Invalid input", 403: "Forbidden"},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a region",
        responses={204: "No Content", 403: "Forbidden", 404: "Not Found"},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class CityViewSet(viewsets.ModelViewSet):
    """
    get:
    List all cities or retrieve a specific city by its ID.

    post:
    Create a new city. Only admins can perform this action.

    put:
    Update a city. Only admins can perform this action.

    delete:
    Delete a city. Only admins can perform this action.
    """

    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsAdminOrReadOnly]

    @swagger_auto_schema(
        operation_description="Retrieve the list of all cities",
        responses={200: CitySerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new city",
        responses={201: CitySerializer, 400: "Invalid input", 403: "Forbidden"},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve a specific city by its ID",
        responses={200: CitySerializer, 404: "Not Found"},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a city",
        responses={200: CitySerializer, 400: "Invalid input", 403: "Forbidden"},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a city",
        responses={204: "No Content", 403: "Forbidden", 404: "Not Found"},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class DistrictViewSet(viewsets.ModelViewSet):
    """
    get:
    List all districts or retrieve a specific district by its ID.

    post:
    Create a new district. Only admins can perform this action.

    put:
    Update a district. Only admins can perform this action.

    delete:
    Delete a district. Only admins can perform this action.
    """

    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [IsAdminOrReadOnly]

    @swagger_auto_schema(
        operation_description="Retrieve the list of all districts",
        responses={200: DistrictSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new district",
        responses={201: DistrictSerializer, 400: "Invalid input", 403: "Forbidden"},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve a specific district by its ID",
        responses={200: DistrictSerializer, 404: "Not Found"},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a district",
        responses={200: DistrictSerializer, 400: "Invalid input", 403: "Forbidden"},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a district",
        responses={204: "No Content", 403: "Forbidden", 404: "Not Found"},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
