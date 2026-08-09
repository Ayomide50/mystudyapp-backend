from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import StudentProfile
from .serializers import StudentProfileSerializer
from common.pagination import StandardResultsSetPagination

class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.select_related('user', 'department').all().order_by('-created_at')
    serializer_class = StudentProfileSerializer
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

        my_referral_code = self.request.query_params.get('my_referral_code')
        if my_referral_code:
            queryset = queryset.filter(my_referral_code=my_referral_code)

        return queryset

    @action(detail=False, methods=['get'])
    def me(self, request):
        profile = self.get_queryset().filter(user=request.user).first()
        if not profile:
            return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=['post', 'put', 'patch'])
    def update_many(self, request):
        department_id = request.data.get('department_id')
        updates = request.data.get('updates', request.data)
        qs = StudentProfile.objects.all()
        if department_id:
            qs = qs.filter(department_id=department_id)
        if isinstance(updates, dict):
            clean_updates = updates.get('$set', updates)
            clean_updates = {k: v for k, v in clean_updates.items() if hasattr(StudentProfile, k)}
            if clean_updates:
                updated_count = qs.update(**clean_updates)
                return Response({'updated': updated_count}, status=status.HTTP_200_OK)
        return Response({'updated': 0}, status=status.HTTP_200_OK)
