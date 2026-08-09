from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReferralViewSet, WithdrawalRequestViewSet

router = DefaultRouter()
router.register(r'referrals', ReferralViewSet, basename='referrals')
router.register(r'withdrawals', WithdrawalRequestViewSet, basename='withdrawals')

urlpatterns = [
    path('', include(router.urls)),
]
