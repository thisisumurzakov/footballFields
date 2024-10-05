from django.db.models.functions import Radians, ACos, Cos, Sin
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F, ExpressionWrapper, FloatField
from django.utils import timezone, dateparse

from accounts.permissions import IsOwnerRoleOrReadOnly

from .models import FootballField, Booking
from .serializers import FootballFieldSerializer, BookingSerializer
from .permissions import IsOwnerOrReadOnly, IsOwner


class FootballFieldListCreateView(generics.ListCreateAPIView):
    """
    get:
    List all football fields. Filter by name or address if needed.

    post:
    Create a new football field. Only owners can create fields.
    """
    queryset = FootballField.objects.all()
    serializer_class = FootballFieldSerializer
    permission_classes = [IsOwnerRoleOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'address']

    @swagger_auto_schema(
        operation_description="Create a new football field",
        responses={
            201: FootballFieldSerializer,
            400: 'Invalid input',
            403: 'Forbidden',
        }
    )
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @swagger_auto_schema(
        operation_description="List all football fields",
        responses={
            200: FootballFieldSerializer(many=True),
            403: 'Forbidden',
        }
    )
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == 'owner':
            return FootballField.objects.filter(owner=user)
        else:
            return FootballField.objects.all()


class FootballFieldDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    get:
    Retrieve the details of a football field by its ID.

    put:
    Update the details of a football field. Only the owner can update.

    delete:
    Delete a football field. Only the owner can delete.
    """
    queryset = FootballField.objects.all()
    serializer_class = FootballFieldSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    @swagger_auto_schema(
        operation_description="Retrieve a football field by its ID",
        responses={200: FootballFieldSerializer, 404: 'Not Found'}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a football field",
        responses={200: FootballFieldSerializer, 403: 'Forbidden', 404: 'Not Found'}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a football field",
        responses={204: 'No Content', 403: 'Forbidden', 404: 'Not Found'}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class BookingListCreateView(generics.ListCreateAPIView):
    """
    get:
    List bookings for the authenticated user (or the owner’s fields).

    post:
    Create a new booking for a field.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['field__name', 'start_time', 'end_time']

    @swagger_auto_schema(
        operation_description="Create a new booking",
        responses={201: BookingSerializer, 400: 'Invalid input', 403: 'Forbidden'}
    )
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="List all bookings for the authenticated user or owner's fields",
        responses={200: BookingSerializer(many=True), 403: 'Forbidden'}
    )
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == 'user':
            return Booking.objects.filter(user=user)
        elif user.is_authenticated and user.role == 'owner':
            return Booking.objects.filter(field__owner=user)
        elif user.is_authenticated and user.role == 'admin':
            return Booking.objects.all()
        else:
            return Booking.objects.none()


class BookingDetailView(generics.RetrieveDestroyAPIView):
    """
    get:
    Retrieve a specific booking.

    delete:
    Delete a specific booking.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend]

    @swagger_auto_schema(
        operation_description="Retrieve a specific booking",
        responses={200: BookingSerializer, 404: 'Not Found'}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a specific booking",
        responses={204: 'No Content', 403: 'Forbidden', 404: 'Not Found'}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class AvailableFieldsListView(generics.ListAPIView):
    """
    get:
    List available football fields. Can filter by district, time range, and proximity to a location.
    """
    queryset = FootballField.objects.all()
    serializer_class = FootballFieldSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'address']

    @swagger_auto_schema(
        operation_description="List available football fields, filterable by district, time range, and location",
        manual_parameters=[
            openapi.Parameter('district_id', openapi.IN_QUERY, description="Filter by district ID",
                              type=openapi.TYPE_INTEGER),
            openapi.Parameter('start_time', openapi.IN_QUERY, description="Filter by start time (ISO format)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('end_time', openapi.IN_QUERY, description="Filter by end time (ISO format)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('latitude', openapi.IN_QUERY, description="Filter by proximity (latitude)",
                              type=openapi.TYPE_NUMBER),
            openapi.Parameter('longitude', openapi.IN_QUERY, description="Filter by proximity (longitude)",
                              type=openapi.TYPE_NUMBER),
        ],
        responses={200: FootballFieldSerializer(many=True), 400: 'Invalid input'}
    )
    def get_queryset(self):
        queryset = super().get_queryset()

        district_id = self.request.query_params.get('district_id')
        if district_id:
            queryset = queryset.filter(district__id=district_id)

        start_time_str = self.request.query_params.get('start_time')
        end_time_str = self.request.query_params.get('end_time')

        if start_time_str and end_time_str:
            try:
                start_time = dateparse.parse_datetime(start_time_str)
                end_time = dateparse.parse_datetime(end_time_str)
                if start_time is None or end_time is None:
                    return queryset.none()
                if timezone.is_naive(start_time):
                    start_time = timezone.make_aware(start_time, timezone.get_current_timezone())
                if timezone.is_naive(end_time):
                    end_time = timezone.make_aware(end_time, timezone.get_current_timezone())
            except (ValueError, TypeError):
                return queryset.none()

            # Exclude fields that are booked during the given time interval
            queryset = queryset.exclude(
                Q(bookings__start_time__lt=end_time) & Q(bookings__end_time__gt=start_time)
            )

            # Filter fields that are open during the requested time
            # Adjusting times to compare time parts only
            requested_start_time = start_time.time()
            requested_end_time = end_time.time()

            # Filter fields where the opening time is before or equal to the requested start time
            # and the closing time is after or equal to the requested end time
            queryset = queryset.filter(
                opening_time__lte=requested_start_time,
                closing_time__gte=requested_end_time
            )

        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')

        if latitude and longitude:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except ValueError:
                return queryset

            # Haversine formula
            distance_expression = ExpressionWrapper(
                ACos(
                    Sin(Radians(F('latitude'))) * Sin(Radians(latitude)) +
                    Cos(Radians(F('latitude'))) * Cos(Radians(latitude)) *
                    Cos(Radians(F('longitude')) - Radians(longitude))
                ) * 6371,  # Radius of Earth in kilometers
                output_field=FloatField()
            )

            queryset = queryset.annotate(distance=distance_expression).order_by('distance')

        return queryset
