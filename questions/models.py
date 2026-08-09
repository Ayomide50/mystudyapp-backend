from django.db import models
from courses.models import Course
from topics.models import Topic
from common.utils import generate_uuid

class Question(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Easy'
        MEDIUM = 'medium', 'Medium'
        HARD = 'hard', 'Hard'

    class CorrectAnswer(models.TextChoices):
        A = 'A', 'Option A'
        B = 'B', 'Option B'
        C = 'C', 'Option C'
        D = 'D', 'Option D'

    id = models.CharField(max_length=64, primary_key=True, default=generate_uuid)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='questions')
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, related_name='questions', null=True, blank=True)
    topic_title = models.CharField('Topic Title Denormalized', max_length=255, blank=True, default='')
    course_code = models.CharField('Course Code Denormalized', max_length=50, blank=True, default='')
    question_text = models.TextField('Question Text')
    option_a = models.TextField('Option A')
    option_b = models.TextField('Option B')
    option_c = models.TextField('Option C')
    option_d = models.TextField('Option D')
    correct_answer = models.CharField('Correct Answer', max_length=5, choices=CorrectAnswer.choices)
    explanation = models.TextField('Explanation', blank=True, default='')
    difficulty = models.CharField('Difficulty', max_length=20, choices=Difficulty.choices, default=Difficulty.MEDIUM, db_index=True)
    is_active = models.BooleanField('Is Active', default=True, db_index=True)
    is_free_trial = models.BooleanField('Is Free Trial', default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'is_active']),
            models.Index(fields=['topic', 'is_active']),
            models.Index(fields=['is_free_trial', 'is_active']),
        ]

    def __str__(self):
        return f"[{self.course_code or self.course.code}] {self.question_text[:50]}..."
