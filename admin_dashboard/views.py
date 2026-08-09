from rest_framework import views, response, status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsSuperAdmin, IsAdmin, IsModerator
from django.contrib.auth import get_user_model
from students.models import StudentProfile
from courses.models import Course
from departments.models import Department
from questions.models import Question
from results.models import MockExamResult
from drf_spectacular.utils import extend_schema

User = get_user_model()

class AdminDashboardStatsView(views.APIView):
    permission_classes = [IsAuthenticated, (IsSuperAdmin | IsAdmin | IsModerator)]

    @extend_schema(responses={200: dict})
    def get(self, request, *args, **kwargs):
        total_students = StudentProfile.objects.count()
        total_courses = Course.objects.count()
        total_departments = Department.objects.count()
        total_questions = Question.objects.count()
        total_mock_exams = MockExamResult.objects.count()

        active_users = User.objects.filter(is_active=True, role=User.Role.STUDENT).count()

        stats = {
            'total_students': total_students,
            'active_students': active_users,
            'total_courses': total_courses,
            'total_departments': total_departments,
            'total_questions': total_questions,
            'total_mock_exams_taken': total_mock_exams,
        }
        
        return response.Response(stats, status=status.HTTP_200_OK)

class VerifyAdminPasswordView(views.APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=dict, responses={200: dict})
    def post(self, request, *args, **kwargs):
        password = request.data.get('password', '')
        user = request.user
        is_valid = bool(
            user.is_staff or 
            user.is_superuser or 
            user.role in [User.Role.SUPER_ADMIN, User.Role.ADMIN] or
            user.check_password(password)
        )
        return response.Response({"authorized": is_valid, "data": {"authorized": is_valid}}, status=status.HTTP_200_OK if is_valid else status.HTTP_400_BAD_REQUEST)

class FunctionInvokeView(views.APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=dict, responses={200: dict})
    def post(self, request, function_name, *args, **kwargs):
        if function_name == "verifyAdminPassword":
            password = request.data.get('password', '')
            user = request.user
            is_valid = bool(
                user.is_staff or 
                user.is_superuser or 
                user.role in [User.Role.SUPER_ADMIN, User.Role.ADMIN] or
                user.check_password(password)
            )
            return response.Response({"data": {"authorized": is_valid}}, status=status.HTTP_200_OK)
        return response.Response({"error": f"Function {function_name} not found."}, status=status.HTTP_404_NOT_FOUND)
