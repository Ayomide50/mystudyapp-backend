from django.db import models
from departments.models import Department
from common.utils import generate_uuid

class Course(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_uuid)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses', null=True, blank=True)
    department_name = models.CharField('Department Name Override', max_length=255, blank=True, default='')
    title = models.CharField('Course Title', max_length=255)
    code = models.CharField('Course Code', max_length=50, db_index=True)
    level = models.CharField('Academic Level', max_length=20, default='100', db_index=True)
    description = models.TextField('Description', blank=True, default='')
    icon = models.CharField('Icon / Emoji', max_length=100, blank=True, default='')
    is_active = models.BooleanField('Is Active', default=True, db_index=True)
    question_count = models.PositiveIntegerField('Question Count', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['code']
        indexes = [
            models.Index(fields=['department', 'level']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.code} - {self.title}"
