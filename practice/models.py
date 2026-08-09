from django.db import models
from django.conf import settings
from courses.models import Course
from topics.models import Topic
from questions.models import Question
from common.utils import generate_uuid

class PracticeSession(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_uuid)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='practice_sessions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='practice_sessions')
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, related_name='practice_sessions', null=True, blank=True)
    course_code = models.CharField('Course Code', max_length=50, blank=True, default='')
    mode = models.CharField('Practice Mode', max_length=50, default='practice')
    
    total_questions = models.PositiveIntegerField('Total Questions', default=0)
    correct_answers = models.PositiveIntegerField('Correct Answers', default=0)
    wrong_answers = models.PositiveIntegerField('Wrong Answers', default=0)
    score_percentage = models.FloatField('Score Percentage', default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Practice Session'
        verbose_name_plural = 'Practice Sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['course', '-created_at']),
        ]

    def __str__(self):
        return f"PracticeSession: User {self.user_id} - Course {self.course_code} - {self.score_percentage}%"

class PracticeAttempt(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_uuid)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='practice_attempts')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='practice_attempts')
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, related_name='practice_attempts', null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='practice_attempts', null=True, blank=True)
    
    course_code = models.CharField('Course Code', max_length=50, blank=True, default='')
    selected_answer = models.CharField('Selected Answer', max_length=10, blank=True, default='')
    correct_answer = models.CharField('Correct Answer', max_length=10, blank=True, default='')
    is_correct = models.BooleanField('Is Correct', default=False)
    time_spent_seconds = models.PositiveIntegerField('Time Spent Seconds', default=0, null=True, blank=True)
    mode = models.CharField('Mode', max_length=50, default='practice')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Practice Attempt'
        verbose_name_plural = 'Practice Attempts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['question', 'user']),
        ]

    def __str__(self):
        return f"Attempt: User {self.user_id} - Q {self.question_id} ({'Correct' if self.is_correct else 'Wrong'})"
