from rest_framework import status, generics, views, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import (
    CustomUserSerializer, RegisterSerializer, CustomTokenObtainPairSerializer,
    ChangePasswordSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)
from .services import create_student_with_profile
from common.pagination import StandardResultsSetPagination

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        full_name = serializer.validated_data.get('full_name', '')
        referral_code = request.data.get('referral_code', '')

        if User.objects.filter(email=email).exists():
            return Response(
                {'success': False, 'message': 'A user with this email already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user, profile = create_student_with_profile(email, password, full_name, referral_code)
        refresh = RefreshToken.for_user(user)

        return Response({
            'success': True,
            'message': 'User registered successfully.',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': CustomUserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

class MeView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomUserSerializer

    @extend_schema(responses={200: CustomUserSerializer})
    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)

class ChangePasswordView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    @extend_schema(request=ChangePasswordSerializer)
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'success': False, 'message': 'Incorrect current password.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'success': True, 'message': 'Password updated successfully.'})

class ForgotPasswordView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer

    @extend_schema(request=ForgotPasswordSerializer)
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        if user:
            return Response({'success': True, 'message': 'Password reset instructions sent to your email.'})
        return Response({'success': True, 'message': 'If an account exists, a reset email was sent.'})

class ResetPasswordView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    @extend_schema(request=ResetPasswordSerializer)
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'success': True, 'message': 'Password has been reset successfully.'})

class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None)
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'success': True, 'message': 'Successfully logged out.'})
        except Exception:
            return Response({'success': True, 'message': 'Logged out.'})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
