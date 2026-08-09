from django.db import models
from courses.models import Course
from common.utils import generate_uuid

class Topic(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_uuid)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField('Topic Title', max_length=255)
    description = models.TextField('Description', blank=True, default='')
    is_active = models.BooleanField('Is Active', default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'
        ordering = ['title']
        indexes = [
            models.Index(fields=['course', 'is_active']),
        ]

    def __str__(self):
        return f"{self.title} ({self.course.code})"
