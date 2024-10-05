from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ActivateUserView,
    CustomTokenObtainPairView,
    LogoutView,
    UserDetailView,
    UserRegistrationView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", UserDetailView.as_view(), name="user_detail"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("activate/", ActivateUserView.as_view(), name="activate"),
]
