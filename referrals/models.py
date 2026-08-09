from django.db import models
from django.conf import settings
from common.utils import generate_uuid

class Referral(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        PAID = 'paid', 'Paid'
        CANCELLED = 'cancelled', 'Cancelled'

    id = models.CharField(max_length=64, primary_key=True, default=generate_uuid)
    referrer_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_referrals')
    referred_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='received_referrals', null=True, blank=True)
    
    referrer_code = models.CharField('Referrer Code', max_length=50, db_index=True)
    referred_email = models.EmailField('Referred Email', blank=True, default='')
    referred_name = models.CharField('Referred Name', max_length=255, blank=True, default='')
    reward_amount = models.DecimalField('Reward Amount', max_digits=10, decimal_places=2, default=500.00)
    
    status = models.CharField('Status', max_length=30, choices=Status.choices, default=Status.PENDING, db_index=True)
    paid_date = models.DateTimeField('Paid Date', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Referral'
        verbose_name_plural = 'Referrals'
        ordering = ['-created_at']

    def __str__(self):
        return f"Referral by {self.referrer_code} -> {self.referred_email}"

class WithdrawalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        PAID = 'paid', 'Paid'

    id = models.CharField(max_length=64, primary_key=True, default=generate_uuid)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawal_requests')
    referral_code = models.CharField('Referral Code', max_length=50, blank=True, default='')
    full_name = models.CharField('Full Name', max_length=255)
    email = models.EmailField('Email Address')
    
    bank_name = models.CharField('Bank Name', max_length=100)
    account_number = models.CharField('Account Number', max_length=50)
    account_name = models.CharField('Account Name', max_length=255)
    amount = models.DecimalField('Withdrawal Amount', max_digits=10, decimal_places=2)
    
    status = models.CharField('Status', max_length=30, choices=Status.choices, default=Status.PENDING, db_index=True)
    paid_date = models.DateTimeField('Paid Date', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Withdrawal Request'
        verbose_name_plural = 'Withdrawal Requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"Withdrawal: {self.full_name} - ₦{self.amount} ({self.status})"
