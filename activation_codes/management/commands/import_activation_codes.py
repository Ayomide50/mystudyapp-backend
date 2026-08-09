import os
import csv
from dateutil import parser as date_parser
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from activation_codes.models import ActivationCode

User = get_user_model()

class Command(BaseCommand):
    help = 'Import activation codes from ActivationCode_export.csv'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default=r'c:\Users\partn\OneDrive\Documents\My study app\baackend data\ActivationCode_export (1).csv')

    def handle(self, *args, **options):
        file_path = options['path']
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Starting import from {file_path}..."))
        count = 0
        created_count = 0

        def parse_date(date_str):
            if not date_str: return None
            try:
                return date_parser.parse(date_str)
            except:
                return None

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    code_val = row.get('code', '').strip()
                    if not code_val:
                        continue

                    status_val = row.get('status', 'unused').strip()
                    access_duration = row.get('access_duration', 'full_time').strip()
                    assigned_email = row.get('assigned_student_email', '').strip()
                    
                    student = User.objects.filter(email=assigned_email).first() if assigned_email else None
                    code_id = row.get('id', '').strip()

                    code_obj, created = ActivationCode.objects.update_or_create(
                        code=code_val,
                        defaults={
                            'id': code_id if code_id else None,
                            'access_duration': access_duration if access_duration in dict(ActivationCode.Duration.choices) else ActivationCode.Duration.FULL_TIME,
                            'status': status_val if status_val in dict(ActivationCode.Status.choices) else ActivationCode.Status.UNUSED,
                            'notes': row.get('notes', '').strip(),
                            'assigned_student': student,
                            'assigned_student_email': assigned_email,
                            'assigned_student_name': row.get('assigned_student_name', '').strip(),
                            'date_activated': parse_date(row.get('date_activated', '')),
                            'is_sample': row.get('is_sample', 'false').lower() == 'true',
                        }
                    )
                    if created:
                        created_count += 1
                    count += 1
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Error importing row: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Activation Codes import finished! Total: {count}, Created: {created_count}"))
