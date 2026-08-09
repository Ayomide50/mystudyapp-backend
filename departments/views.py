from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Department
from .serializers import DepartmentSerializer
from common.pagination import StandardResultsSetPagination

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by('name')
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset

    @action(detail=False, methods=['post', 'put', 'patch'])
    def update_many(self, request):
        updates = request.data.get('updates', request.data)
        qs = Department.objects.all()
        if isinstance(updates, dict):
            clean_updates = updates.get('$set', updates)
            clean_updates = {k: v for k, v in clean_updates.items() if hasattr(Department, k)}
            if clean_updates:
                updated_count = qs.update(**clean_updates)
                return Response({'updated': updated_count}, status=status.HTTP_200_OK)
        return Response({'updated': 0}, status=status.HTTP_200_OK)
