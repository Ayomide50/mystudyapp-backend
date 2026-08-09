from rest_framework import serializers
from .models import Referral, WithdrawalRequest
from accounts.serializers import CustomUserSerializer

class ReferralSerializer(serializers.ModelSerializer):
    referrer_user = CustomUserSerializer(read_only=True)
    referred_user = CustomUserSerializer(read_only=True)

    class Meta:
        model = Referral
        fields = (
            'id', 'referrer_user', 'referred_user', 'referrer_code', 
            'referred_email', 'referred_name', 'reward_amount', 'status', 
            'paid_date', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

class WithdrawalRequestSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)

    class Meta:
        model = WithdrawalRequest
        fields = (
            'id', 'user', 'referral_code', 'full_name', 'email', 
            'bank_name', 'account_number', 'account_name', 'amount', 
            'status', 'paid_date', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
