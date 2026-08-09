from django.db import models
from django.conf import settings
from courses.models import Course
from questions.models import Question
from common.utils import generate_uuid

class Bookmark(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_uuid)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='bookmarks')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='bookmarks')
    course_code = models.CharField('Course Code', max_length=50, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bookmark'
        verbose_name_plural = 'Bookmarks'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'question'], name='unique_user_question_bookmark')
        ]
        indexes = [
            models.Index(fields=['user', 'course']),
        ]

    def __str__(self):
        return f"Bookmark: User {self.user_id} - Q {self.question_id}"
