from rest_framework import serializers
from .models import Course
from departments.serializers import DepartmentSerializer

class CourseSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Course
        fields = (
            'id', 'code', 'title', 'description', 'level',
            'icon', 'question_count', 'is_active',
            'department', 'department_id', 'department_name',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

