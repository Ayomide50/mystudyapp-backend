from rest_framework import serializers
from .models import MockExamResult
from courses.serializers import CourseSerializer

class MockExamResultSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    course_id = serializers.CharField(write_only=True)

    class Meta:
        model = MockExamResult
        fields = (
            'id', 'course', 'course_id', 'course_code', 'total_questions',
            'correct_answers', 'wrong_answers', 'unanswered', 'score_percentage',
            'time_spent_seconds', 'time_allowed_seconds', 'passed', 'answers',
            'created_at'
        )
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
