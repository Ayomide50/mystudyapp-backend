from rest_framework import serializers
from .models import Bookmark
from courses.serializers import CourseSerializer
from questions.serializers import QuestionSerializer

class BookmarkSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    course_id = serializers.CharField(write_only=True)
    question = QuestionSerializer(read_only=True)
    question_id = serializers.CharField(write_only=True)

    class Meta:
        model = Bookmark
        fields = ('id', 'course', 'course_id', 'question', 'question_id', 'course_code', 'created_at')
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
