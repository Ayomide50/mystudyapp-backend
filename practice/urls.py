from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PracticeSessionViewSet, PracticeAttemptViewSet

router = DefaultRouter()
router.register(r'sessions', PracticeSessionViewSet, basename='practice-sessions')
router.register(r'attempts', PracticeAttemptViewSet, basename='practice-attempts')

urlpatterns = [
    path('', include(router.urls)),
]
