import os
import csv
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from bookmarks.models import Bookmark
from courses.models import Course
from questions.models import Question

User = get_user_model()

class Command(BaseCommand):
    help = 'Import bookmarks from Bookmark_export.csv'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default=r'c:\Users\partn\OneDrive\Documents\My study app\baackend data\Bookmark_export (1).csv')

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
                    question_id = row.get('question_id', '').strip()
                    course_id = row.get('course_id', '').strip()

                    if not user_id or not question_id or not course_id:
                        continue

                    user = User.objects.filter(id=user_id).first()
                    question = Question.objects.filter(id=question_id).first()
                    course = Course.objects.filter(id=course_id).first()

                    if not user or not question or not course:
                        continue
                    
                    bookmark_id = row.get('id', '').strip()

                    bookmark, created = Bookmark.objects.update_or_create(
                        user=user,
                        question=question,
                        defaults={
                            'id': bookmark_id if bookmark_id else None,
                            'course': course,
                            'course_code': row.get('course_code', '').strip() or course.code
                        }
                    )
                    if created:
                        created_count += 1
                    count += 1
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Error importing bookmark: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Bookmarks import finished! Total processed: {count}, Created: {created_count}"))
