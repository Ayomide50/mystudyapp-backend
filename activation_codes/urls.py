from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActivationCodeViewSet

router = DefaultRouter()
router.register(r'', ActivationCodeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
