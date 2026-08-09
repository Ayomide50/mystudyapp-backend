import os
import csv
import json
from django.core.management.base import BaseCommand
from departments.models import Department

class Command(BaseCommand):
    help = 'Import departments from Department_export.csv'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default=r'c:\Users\partn\OneDrive\Documents\My study app\baackend data\Department_export.csv')

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
                    dept_id = row.get('id', '').strip()
                    name = row.get('name', '').strip()
                    if not name:
                        continue
                    description = row.get('description', '').strip()
                    is_active = row.get('is_active', 'true').lower() == 'true'
                    levels_str = row.get('levels', '[]').strip()
                    
                    try:
                        levels = json.loads(levels_str)
                    except Exception:
                        levels = ["100"]

                    dept, created = Department.objects.update_or_create(
                        id=dept_id if dept_id else None,
                        defaults={
                            'name': name,
                            'description': description,
                            'is_active': is_active,
                            'levels': levels,
                        }
                    )
                    if created:
                        created_count += 1
                    count += 1
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Error importing row {row}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Departments import finished! Total: {count}, Created: {created_count}"))
