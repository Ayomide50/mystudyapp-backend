import os
import csv
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Import users from mystudyapp-users.csv'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default=r'c:\Users\partn\OneDrive\Documents\My study app\baackend data\mystudyapp-users.csv')

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
                    email = row.get('email', '').strip()
                    if not email:
                        continue
                    
                    full_name = row.get('full_name', '').strip()
                    role = row.get('role', 'user').strip()
                    status_val = row.get('status', 'active').strip()

                    role_mapping = {
                        'admin': User.Role.ADMIN,
                        'super_admin': User.Role.SUPER_ADMIN,
                        'moderator': User.Role.MODERATOR,
                        'instructor': User.Role.INSTRUCTOR,
                        'user': User.Role.STUDENT,
                        'student': User.Role.STUDENT,
                    }
                    user_role = role_mapping.get(role, User.Role.STUDENT)

                    user, created = User.objects.update_or_create(
                        email=email,
                        defaults={
                            'username': email,
                            'full_name': full_name,
                            'role': user_role,
                            'status': status_val if status_val in ['active', 'inactive', 'suspended'] else 'active',
                            'is_staff': user_role in [User.Role.ADMIN, User.Role.SUPER_ADMIN],
                            'is_superuser': user_role == User.Role.SUPER_ADMIN,
                        }
                    )
                    if created:
                        user.set_password("StudyApp2026!")
                        user.save()
                        created_count += 1
                    count += 1
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Error processing row {row}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Import finished! Processed: {count}, Created: {created_count}"))
