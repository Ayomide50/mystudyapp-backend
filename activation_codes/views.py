from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import ActivationCode
from .serializers import ActivationCodeSerializer
from common.pagination import StandardResultsSetPagination

class ActivationCodeViewSet(viewsets.ModelViewSet):
    queryset = ActivationCode.objects.all().order_by('-created_at')
    serializer_class = ActivationCodeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(assigned_student=self.request.user)

        code = self.request.query_params.get('code')
        if code:
            queryset = queryset.filter(code__iexact=code.strip())

        return queryset

    @action(detail=False, methods=['post'])
    def verify(self, request):
        code = request.data.get('code')
        if not code:
            return Response({"detail": "Code is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        activation_code = ActivationCode.objects.filter(code=code).first()
        if not activation_code:
            return Response({"detail": "Invalid activation code."}, status=status.HTTP_404_NOT_FOUND)
            
        return Response({
            "status": activation_code.status,
            "access_duration": activation_code.access_duration
        })

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        codes_data = request.data if isinstance(request.data, list) else request.data.get('codes', [])
        created_objs = []
        for item in codes_data:
            serializer = self.get_serializer(data=item)
            if serializer.is_valid():
                created_objs.append(ActivationCode(**serializer.validated_data))
        if created_objs:
            ActivationCode.objects.bulk_create(created_objs)
        return Response({'created': len(created_objs)}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post', 'delete'])
    def delete_many(self, request):
        status_filter = request.data.get('status') or request.query_params.get('status')
        qs = self.get_queryset()
        if status_filter:
            qs = qs.filter(status=status_filter)
        count = qs.count()
        qs.delete()
        return Response({"deleted": count}, status=status.HTTP_200_OK)
