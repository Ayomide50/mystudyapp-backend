from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import MockExamResult
from .serializers import MockExamResultSerializer
from common.pagination import StandardResultsSetPagination

class MockExamResultViewSet(viewsets.ModelViewSet):
    queryset = MockExamResult.objects.select_related('user', 'course').all().order_by('-created_at')
    serializer_class = MockExamResultSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        else:
            user_id = self.request.query_params.get('user_id')
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
            
        return queryset

    @action(detail=False, methods=['post', 'delete'])
    def delete_many(self, request):
        user_id = request.data.get('user_id') or request.query_params.get('user_id')
        qs = self.get_queryset()
        if user_id:
            qs = qs.filter(user_id=user_id)
        count = qs.count()
        qs.delete()
        return Response({"deleted": count}, status=status.HTTP_200_OK)

