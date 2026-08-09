from django.db import models
from django.conf import settings
from courses.models import Course
from common.utils import generate_uuid

class MockExamResult(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_uuid)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mock_exam_results')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='mock_exam_results')
    course_code = models.CharField('Course Code', max_length=50, blank=True, default='')
    
    total_questions = models.PositiveIntegerField('Total Questions', default=0)
    correct_answers = models.PositiveIntegerField('Correct Answers', default=0)
    wrong_answers = models.PositiveIntegerField('Wrong Answers', default=0)
    unanswered = models.PositiveIntegerField('Unanswered Questions', default=0)
    score_percentage = models.FloatField('Score Percentage', default=0.0)
    
    time_spent_seconds = models.PositiveIntegerField('Time Spent (seconds)', default=0)
    time_allowed_seconds = models.PositiveIntegerField('Time Allowed (seconds)', default=0)
    passed = models.BooleanField('Passed Exam', default=False, db_index=True)
    answers = models.JSONField('Submitted Answers Data', default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mock Exam Result'
        verbose_name_plural = 'Mock Exam Results'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['course', '-created_at']),
        ]

    def __str__(self):
        return f"MockExam: User {self.user_id} - Course {self.course_code} - {self.score_percentage}%"
