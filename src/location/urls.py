from rest_framework.routers import DefaultRouter
from .views import RegionViewSet, CityViewSet, DistrictViewSet

router = DefaultRouter()
router.register(r'regions', RegionViewSet)
router.register(r'cities', CityViewSet)
router.register(r'districts', DistrictViewSet)

urlpatterns = router.urls
