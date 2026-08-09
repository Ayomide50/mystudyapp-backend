import os
import csv
from django.core.management.base import BaseCommand
from courses.models import Course
from departments.models import Department

class Command(BaseCommand):
    help = 'Import courses from Course_export.csv'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default=r'c:\Users\partn\OneDrive\Documents\My study app\baackend data\Course_export.csv')

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
                    course_id = row.get('id', '').strip()
                    code = row.get('code', '').strip()
                    title = row.get('title', '').strip() or code
                    dept_id = row.get('department_id', '').strip()
                    dept_name = row.get('department_name', '').strip()
                    level = row.get('level', '100').strip()
                    description = row.get('description', '').strip()
                    icon = row.get('icon', '').strip()
                    is_active = row.get('is_active', 'true').lower() == 'true'
                    q_count = int(row.get('question_count', '0') or 0)

                    department = Department.objects.filter(id=dept_id).first()

                    course, created = Course.objects.update_or_create(
                        id=course_id if course_id else None,
                        defaults={
                            'title': title,
                            'code': code,
                            'department': department,
                            'department_name': dept_name,
                            'level': level,
                            'description': description,
                            'icon': icon,
                            'is_active': is_active,
                            'question_count': q_count,
                        }
                    )
                    if created:
                        created_count += 1
                    count += 1
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Error importing course row {row}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Courses import finished! Total: {count}, Created: {created_count}"))
