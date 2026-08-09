from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Question
from .serializers import QuestionSerializer
from common.pagination import StandardResultsSetPagination

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.select_related('course', 'topic').all().order_by('-created_at')
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)

        question_id = self.request.query_params.get('id')
        if question_id:
            if ',' in question_id:
                ids = [i.strip() for i in question_id.split(',') if i.strip()]
                queryset = queryset.filter(id__in=ids)
            else:
                queryset = queryset.filter(id=question_id)
            
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
            
        topic_id = self.request.query_params.get('topic_id')
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
            
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        is_free_trial = self.request.query_params.get('is_free_trial')
        if is_free_trial is not None:
            queryset = queryset.filter(is_free_trial=is_free_trial.lower() == 'true')
            
        return queryset

