import os
import csv
import json
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.db import connection
from django.conf import settings

class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_ok = True
        except Exception:
            db_ok = False

        status_code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response({
            "status": "healthy" if db_ok else "unhealthy",
            "database": "connected" if db_ok else "disconnected"
        }, status=status_code)

class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file') or request.FILES.get('upload')
        if not file_obj:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        filename = f"{uuid.uuid4().hex[:10]}_{file_obj.name}"
        filepath = os.path.join(upload_dir, filename)

        with open(filepath, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        file_url = f"{settings.MEDIA_URL}uploads/{filename}"
        return Response({
            'file_url': file_url,
            'url': file_url,
            'filename': filename,
            'status': 'success'
        }, status=status.HTTP_201_CREATED)

class ExtractDataView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        file_url = request.data.get('file_url', '')
        if not file_url:
            return Response({'status': 'error', 'message': 'file_url required'}, status=status.HTTP_400_BAD_REQUEST)

        # Resolve relative media URL to local disk path
        clean_path = file_url.replace(settings.MEDIA_URL, '').lstrip('/')
        filepath = os.path.join(settings.MEDIA_ROOT, clean_path)

        extracted = []
        if os.path.exists(filepath):
            ext = os.path.splitext(filepath)[1].lower()
            if ext == '.csv':
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.DictReader(f)
                    extracted = [row for row in reader]
            elif ext in ('.json', '.js'):
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    extracted = json.load(f)

        return Response({
            'status': 'success',
            'output': extracted
        }, status=status.HTTP_200_OK)
