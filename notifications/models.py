from django.db import models
from django.conf import settings
from common.utils import generate_uuid

class Notification(models.Model):
    class NotificationType(models.TextChoices):
        INFO = 'info', 'Information'
        SUCCESS = 'success', 'Success'
        WARNING = 'warning', 'Warning'
        SYSTEM = 'system', 'System Broadcast'

    id = models.CharField(max_length=64, primary_key=True, default=generate_uuid)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    title = models.CharField('Title', max_length=255)
    message = models.TextField('Message Content')
    type = models.CharField('Notification Type', max_length=30, choices=NotificationType.choices, default=NotificationType.INFO)
    is_read = models.BooleanField('Is Read', default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification: {self.title} ({'Read' if self.is_read else 'Unread'})"
