from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MockExamResultViewSet

router = DefaultRouter()
router.register(r'', MockExamResultViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
