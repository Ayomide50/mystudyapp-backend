from rest_framework import serializers
from .models import ActivationCode
from accounts.serializers import CustomUserSerializer

class ActivationCodeSerializer(serializers.ModelSerializer):
    assigned_student = CustomUserSerializer(read_only=True)

    class Meta:
        model = ActivationCode
        fields = (
            'id', 'code', 'access_duration', 'status', 'notes', 
            'assigned_student', 'assigned_student_email', 'assigned_student_name', 
            'date_activated', 'is_sample', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
