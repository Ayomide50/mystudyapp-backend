from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Topic
from .serializers import TopicSerializer
from common.pagination import StandardResultsSetPagination

class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all().order_by('title')
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
            
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
            
        return queryset
