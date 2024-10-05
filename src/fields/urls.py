from django.urls import path
from .views import (
    FootballFieldListCreateView, FootballFieldDetailView,
    BookingListCreateView, BookingDetailView,
    AvailableFieldsListView,
)

urlpatterns = [
    path('fields/', FootballFieldListCreateView.as_view(), name='field-list'),
    path('fields/<int:pk>/', FootballFieldDetailView.as_view(), name='field-detail'),
    path('bookings/', BookingListCreateView.as_view(), name='booking-list'),
    path('bookings/<int:pk>/', BookingDetailView.as_view(), name='booking-detail'),
    path('available-fields/', AvailableFieldsListView.as_view(), name='available-fields'),
]
