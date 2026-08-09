from rest_framework import serializers
from .models import PracticeSession, PracticeAttempt
from courses.serializers import CourseSerializer
from topics.serializers import TopicSerializer
from questions.serializers import QuestionSerializer

class PracticeSessionSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    course_id = serializers.CharField(write_only=True)
    topic = TopicSerializer(read_only=True)
    topic_id = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = PracticeSession
        fields = (
            'id', 'course', 'course_id', 'topic', 'topic_id', 'course_code',
            'mode', 'total_questions', 'correct_answers', 'wrong_answers',
            'score_percentage', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class PracticeAttemptSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    course_id = serializers.CharField(write_only=True)
    topic = TopicSerializer(read_only=True)
    topic_id = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    question = QuestionSerializer(read_only=True)
    question_id = serializers.CharField(write_only=True)

    class Meta:
        model = PracticeAttempt
        fields = (
            'id', 'course', 'course_id', 'topic', 'topic_id', 'question', 'question_id',
            'course_code', 'selected_answer', 'correct_answer', 'is_correct',
            'time_spent_seconds', 'mode', 'created_at'
        )
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
