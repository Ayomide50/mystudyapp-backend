from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.permissions import AllowAny

from common.views import HealthCheckView, FileUploadView, ExtractDataView

urlpatterns = [
    # Health Check
    path('api/health/', HealthCheckView.as_view(), name='health_check'),

    # Integration Endpoints (File Upload & Extraction)
    path('api/integrations/upload/', FileUploadView.as_view(), name='file_upload'),
    path('api/integrations/Core/UploadFile', FileUploadView.as_view(), name='file_upload_core'),
    path('api/integrations/extract-data/', ExtractDataView.as_view(), name='extract_data'),
    path('api/integrations/Core/ExtractDataFromUploadedFile', ExtractDataView.as_view(), name='extract_data_core'),

    # OpenAPI Documentation
    path('api/schema/', SpectacularAPIView.as_view(permission_classes=[AllowAny]), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[AllowAny]), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema', permission_classes=[AllowAny]), name='redoc'),

    # Admin
    path('admin/', admin.site.urls),
    
    # Auth Endpoints
    path('api/auth/', include('accounts.urls')),
    
    # Admin Endpoints (Custom React Dashboard)
    path('api/admin/', include('admin_dashboard.urls')),

    # API Endpoints
    path('api/departments/', include('departments.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/topics/', include('topics.urls')),
    path('api/questions/', include('questions.urls')),
    path('api/students/', include('students.urls')),
    path('api/bookmarks/', include('bookmarks.urls')),
    path('api/results/', include('results.urls')),
    path('api/practice/', include('practice.urls')),
    path('api/referrals/', include('referrals.urls')),
    path('api/activation-codes/', include('activation_codes.urls')),
    path('api/notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
