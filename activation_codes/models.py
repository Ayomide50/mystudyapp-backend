from django.db import models
from django.conf import settings
from common.utils import generate_uuid

class ActivationCode(models.Model):
    class Status(models.TextChoices):
        UNUSED = 'unused', 'Unused'
        ACTIVE = 'active', 'Active'
        USED = 'used', 'Used'
        EXPIRED = 'expired', 'Expired'
        REVOKED = 'revoked', 'Revoked'

    class Duration(models.TextChoices):
        ONE_MONTH = '1_month', '1 Month'
        THREE_MONTHS = '3_months', '3 Months'
        SIX_MONTHS = '6_months', '6 Months'
        FULL_TIME = 'full_time', 'Full Time'

    id = models.CharField(max_length=64, primary_key=True, default=generate_uuid)
    code = models.CharField('Activation Code', max_length=100, unique=True, db_index=True)
    access_duration = models.CharField('Access Duration', max_length=50, choices=Duration.choices, default=Duration.FULL_TIME)
    status = models.CharField('Status', max_length=30, choices=Status.choices, default=Status.UNUSED, db_index=True)
    notes = models.TextField('Notes', blank=True, default='')

    assigned_student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='activation_codes', null=True, blank=True)
    assigned_student_email = models.EmailField('Assigned Student Email', blank=True, default='')
    assigned_student_name = models.CharField('Assigned Student Name', max_length=255, blank=True, default='')
    date_activated = models.DateTimeField('Activation Date', null=True, blank=True)

    is_sample = models.BooleanField('Is Sample Code', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Activation Code'
        verbose_name_plural = 'Activation Codes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} ({self.status})"
