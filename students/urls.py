from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentProfileViewSet

router = DefaultRouter()
router.register(r'', StudentProfileViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
