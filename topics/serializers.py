from rest_framework import serializers
from .models import Topic
from courses.serializers import CourseSerializer

class TopicSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    course_id = serializers.CharField(write_only=True)

    class Meta:
        model = Topic
        fields = ('id', 'course', 'course_id', 'title', 'description', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
