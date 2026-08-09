from django.db import models
from common.utils import generate_uuid

class Department(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_uuid)
    name = models.CharField('Department Name', max_length=255, unique=True, db_index=True)
    description = models.TextField('Description', blank=True, default='')
    is_active = models.BooleanField('Is Active', default=True, db_index=True)
    levels = models.JSONField('Available Levels', default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        ordering = ['name']

    def __str__(self):
        return self.name
