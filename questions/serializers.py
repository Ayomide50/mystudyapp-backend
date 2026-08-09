from rest_framework import serializers
from .models import Question
from courses.serializers import CourseSerializer
from topics.serializers import TopicSerializer

class QuestionSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    course_id = serializers.CharField(write_only=True)
    topic = TopicSerializer(read_only=True)
    topic_id = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Question
        fields = (
            'id', 'course', 'course_id', 'topic', 'topic_id',
            'course_code', 'topic_title',
            'question_text', 'option_a', 'option_b', 'option_c', 'option_d',
            'correct_answer', 'explanation', 'difficulty',
            'is_active', 'is_free_trial',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
