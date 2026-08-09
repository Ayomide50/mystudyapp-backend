import os
import csv
from django.core.management.base import BaseCommand
from questions.models import Question
from courses.models import Course
from topics.models import Topic

class Command(BaseCommand):
    help = 'Import questions from Question_export.csv'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default=r'c:\Users\partn\OneDrive\Documents\My study app\baackend data\Question_export.csv')

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
                    q_id = row.get('id', '').strip()
                    course_id = row.get('course_id', '').strip()
                    question_text = row.get('question_text', '').strip()
                    if not question_text or not course_id:
                        continue

                    course = Course.objects.filter(id=course_id).first()
                    if not course:
                        continue

                    topic_id = row.get('topic_id', '').strip()
                    topic = Topic.objects.filter(id=topic_id).first() if topic_id else None

                    q_obj, created = Question.objects.update_or_create(
                        id=q_id if q_id else None,
                        defaults={
                            'course': course,
                            'topic': topic,
                            'topic_title': row.get('topic_title', '').strip(),
                            'course_code': row.get('course_code', '').strip() or course.code,
                            'question_text': question_text,
                            'option_a': row.get('option_a', '').strip(),
                            'option_b': row.get('option_b', '').strip(),
                            'option_c': row.get('option_c', '').strip(),
                            'option_d': row.get('option_d', '').strip(),
                            'correct_answer': row.get('correct_answer', 'A').strip().upper()[:1],
                            'explanation': row.get('explanation', '').strip(),
                            'difficulty': row.get('difficulty', 'medium').strip().lower(),
                            'is_active': row.get('is_active', 'true').lower() == 'true',
                            'is_free_trial': row.get('is_free_trial', 'false').lower() == 'true',
                        }
                    )
                    if created:
                        created_count += 1
                    count += 1
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Error importing question row: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Questions import finished! Total: {count}, Created: {created_count}"))
