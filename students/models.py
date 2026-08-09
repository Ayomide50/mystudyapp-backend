from django.db import models
from django.conf import settings
from departments.models import Department
from common.utils import generate_uuid

class StudentProfile(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_uuid)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, related_name='students', null=True, blank=True)
    department_name = models.CharField('Department Name', max_length=255, blank=True, default='')
    level = models.CharField('Academic Level', max_length=20, default='100', db_index=True)
    
    full_name = models.CharField('Full Name', max_length=255, blank=True, default='')
    email = models.EmailField('Email Address', blank=True, default='')
    profile_image = models.TextField('Profile Image URL', blank=True, default='')
    
    my_referral_code = models.CharField('My Referral Code', max_length=50, blank=True, default='', db_index=True)
    referral_code = models.CharField('Referred By Code', max_length=50, blank=True, default='')
    
    is_activated = models.BooleanField('Is Account Activated', default=False, db_index=True)
    activation_code = models.CharField('Activation Code Used', max_length=100, blank=True, default='')
    activation_date = models.DateTimeField('Activation Date', null=True, blank=True)
    access_expires = models.DateTimeField('Access Expiration Date', null=True, blank=True)
    free_trial_used = models.JSONField('Free Trial Used', default=dict, blank=True)

    total_questions_answered = models.PositiveIntegerField('Total Questions Answered', default=0)
    total_correct = models.PositiveIntegerField('Total Correct Answers', default=0)
    total_practice_sessions = models.PositiveIntegerField('Total Practice Sessions', default=0)
    total_mock_exams = models.PositiveIntegerField('Total Mock Exams', default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"StudentProfile: {self.full_name or self.user.email}"
