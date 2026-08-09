import os
import csv
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from results.models import MockExamResult
from courses.models import Course

User = get_user_model()

class Command(BaseCommand):
    help = 'Import mock exam results from MockExamResult_export.csv'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default=r'c:\Users\partn\OneDrive\Documents\My study app\baackend data\MockExamResult_export.csv')

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
                    course_id = row.get('course_id', '').strip()

                    if not user_id or not course_id:
                        continue

                    user = User.objects.filter(id=user_id).first()
                    course = Course.objects.filter(id=course_id).first()
                    
                    if not user or not course:
                        continue
                        
                    result_id = row.get('id', '').strip()
                    answers_str = row.get('answers', '{}').strip()
                    try:
                        answers_data = json.loads(answers_str) if answers_str else {}
                    except json.JSONDecodeError:
                        answers_data = {}

                    result, created = MockExamResult.objects.update_or_create(
                        id=result_id if result_id else None,
                        defaults={
                            'user': user,
                            'course': course,
                            'course_code': row.get('course_code', '').strip() or course.code,
                            'total_questions': int(row.get('total_questions', '0') or 0),
                            'correct_answers': int(row.get('correct_answers', '0') or 0),
                            'wrong_answers': int(row.get('wrong_answers', '0') or 0),
                            'unanswered': int(row.get('unanswered', '0') or 0),
                            'score_percentage': float(row.get('score_percentage', '0.0') or 0.0),
                            'time_spent_seconds': int(row.get('time_spent_seconds', '0') or 0),
                            'time_allowed_seconds': int(row.get('time_allowed_seconds', '0') or 0),
                            'passed': row.get('passed', 'false').lower() == 'true',
                            'answers': answers_data,
                        }
                    )
                    if created:
                        created_count += 1
                    count += 1
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Error importing mock exam result: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Mock Exam Results import finished! Total: {count}, Created: {created_count}"))
