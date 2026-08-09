import os
import csv
from dateutil import parser as date_parser
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from students.models import StudentProfile
from departments.models import Department
from common.utils import generate_uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Import student profiles from StudentProfile_export.csv'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default=r'c:\Users\partn\OneDrive\Documents\My study app\baackend data\StudentProfile_export.csv')

    def handle(self, *args, **options):
        file_path = options['path']
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Starting import from {file_path}..."))
        count = 0
        created_count = 0

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    user_id = row.get('user_id', '').strip()
                    email = row.get('email', '').strip()
                    if not email:
                        continue

                    user = User.objects.filter(email=email).first()
                    if not user:
                        # Fallback to creating a basic user if not exists from users export
                        user, _ = User.objects.get_or_create(
                            email=email,
                            defaults={
                                'username': email,
                                'full_name': row.get('full_name', '').strip(),
                                'role': User.Role.STUDENT,
                                'status': User.Status.ACTIVE,
                            }
                        )
                        user.set_unusable_password()
                        user.save()

                    dept_id = row.get('department_id', '').strip()
                    department = Department.objects.filter(id=dept_id).first() if dept_id else None

                    def parse_date(date_str):
                        if not date_str: return None
                        try:
                            return date_parser.parse(date_str)
                        except:
                            return None

                    profile_id = row.get('id', '').strip()
                    
                    profile, created = StudentProfile.objects.update_or_create(
                        user=user,
                        defaults={
                            'id': profile_id if profile_id else generate_uuid(),
                            'department': department,
                            'department_name': row.get('department_name', '').strip(),
                            'level': row.get('level', '100').strip(),
                            'full_name': row.get('full_name', '').strip(),
                            'email': email,
                            'profile_image': row.get('profile_image', '').strip(),
                            'my_referral_code': row.get('my_referral_code', '').strip(),
                            'referral_code': row.get('referral_code', '').strip(),
                            'is_activated': row.get('is_activated', 'false').lower() == 'true',
                            'activation_code': row.get('activation_code', '').strip(),
                            'activation_date': parse_date(row.get('activation_date', '')),
                            'access_expires': parse_date(row.get('access_expires', '')),
                            'free_trial_used': row.get('free_trial_used', 'false').lower() == 'true',
                            'total_questions_answered': int(row.get('total_questions_answered', '0') or 0),
                            'total_correct': int(row.get('total_correct', '0') or 0),
                            'total_practice_sessions': int(row.get('total_practice_sessions', '0') or 0),
                            'total_mock_exams': int(row.get('total_mock_exams', '0') or 0),
                        }
                    )
                    if created:
                        created_count += 1
                    count += 1
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Error importing student row: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Students import finished! Total: {count}, Created: {created_count}"))
