from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Referral, WithdrawalRequest
from .serializers import ReferralSerializer, WithdrawalRequestSerializer
from common.pagination import StandardResultsSetPagination

class ReferralViewSet(viewsets.ModelViewSet):
    queryset = Referral.objects.select_related('referrer_user', 'referred_user').all().order_by('-created_at')
    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(referrer_user=self.request.user)
        else:
            referrer_user_id = self.request.query_params.get('referrer_user_id')
            if referrer_user_id:
                queryset = queryset.filter(referrer_user_id=referrer_user_id)

        referred_user_id = self.request.query_params.get('referred_user_id')
        if referred_user_id:
            queryset = queryset.filter(referred_user_id=referred_user_id)

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset

class WithdrawalRequestViewSet(viewsets.ModelViewSet):
    queryset = WithdrawalRequest.objects.select_related('user').all().order_by('-created_at')
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        else:
            user_id = self.request.query_params.get('user_id')
            if user_id:
                queryset = queryset.filter(user=self.request.user_id if user_id == 'me' else user_id)

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset

