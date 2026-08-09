from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminDashboardStatsView, VerifyAdminPasswordView, FunctionInvokeView

from students.views import StudentProfileViewSet
from departments.views import DepartmentViewSet
from courses.views import CourseViewSet
from topics.views import TopicViewSet
from questions.views import QuestionViewSet
from activation_codes.views import ActivationCodeViewSet
from referrals.views import ReferralViewSet, WithdrawalRequestViewSet
from accounts.views import UserViewSet

router = DefaultRouter()
router.register(r'students', StudentProfileViewSet, basename='admin-students')
router.register(r'departments', DepartmentViewSet, basename='admin-departments')
router.register(r'courses', CourseViewSet, basename='admin-courses')
router.register(r'topics', TopicViewSet, basename='admin-topics')
router.register(r'questions', QuestionViewSet, basename='admin-questions')
router.register(r'activation-codes', ActivationCodeViewSet, basename='admin-activation-codes')
router.register(r'referrals', ReferralViewSet, basename='admin-referrals')
router.register(r'withdrawal-requests', WithdrawalRequestViewSet, basename='admin-withdrawal-requests')
router.register(r'users', UserViewSet, basename='admin-users')

urlpatterns = [
    path('dashboard/stats/', AdminDashboardStatsView.as_view(), name='admin_dashboard_stats'),
    path('verify-password/', VerifyAdminPasswordView.as_view(), name='admin_verify_password'),
    path('functions/invoke/<str:function_name>/', FunctionInvokeView.as_view(), name='admin_function_invoke'),
    path('', include(router.urls)),
]

