from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Course
from .serializers import CourseSerializer
from common.pagination import StandardResultsSetPagination

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.select_related('department').all().order_by('code')
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)

        course_id = self.request.query_params.get('id')
        if course_id:
            queryset = queryset.filter(id=course_id)
            
        department_id = self.request.query_params.get('department_id')
        if department_id:
            queryset = queryset.filter(department_id=department_id)

        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset

    @action(detail=False, methods=['post', 'put', 'patch'])
    def update_many(self, request):
        department_id = request.data.get('department_id')
        updates = request.data.get('updates', request.data)
        qs = Course.objects.all()
        if department_id:
            qs = qs.filter(department_id=department_id)
        if isinstance(updates, dict):
            clean_updates = updates.get('$set', updates)
            clean_updates = {k: v for k, v in clean_updates.items() if hasattr(Course, k)}
            if clean_updates:
                updated_count = qs.update(**clean_updates)
                return Response({'updated': updated_count}, status=status.HTTP_200_OK)
        return Response({'updated': 0}, status=status.HTTP_200_OK)
