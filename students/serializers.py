from rest_framework import serializers
from .models import StudentProfile
from accounts.serializers import CustomUserSerializer
from departments.serializers import DepartmentSerializer

class StudentProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = StudentProfile
        fields = (
            'id', 'user', 'department', 'department_id', 'department_name', 
            'level', 'full_name', 'email', 'profile_image', 'my_referral_code', 
            'referral_code', 'is_activated', 'activation_code', 'activation_date', 
            'access_expires', 'free_trial_used', 'total_questions_answered', 
            'total_correct', 'total_practice_sessions', 'total_mock_exams', 
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'user', 'my_referral_code', 'is_activated', 'activation_date', 
            'access_expires', 'free_trial_used', 'total_questions_answered', 
            'total_correct', 'total_practice_sessions', 'total_mock_exams', 
            'created_at', 'updated_at'
        )
