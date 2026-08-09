import os
import csv
from django.core.management.base import BaseCommand
from topics.models import Topic
from courses.models import Course

class Command(BaseCommand):
    help = 'Import topics from Topic_export.csv and Question_export.csv'

    def add_arguments(self, parser):
        parser.add_argument('--topic-path', type=str, default=r'c:\Users\partn\OneDrive\Documents\My study app\baackend data\Topic_export.csv')
        parser.add_argument('--question-path', type=str, default=r'c:\Users\partn\OneDrive\Documents\My study app\baackend data\Question_export.csv')

    def handle(self, *args, **options):
        topic_path = options['topic-path']
        question_path = options['question-path']
        
        count = 0
        created_count = 0

        # Try Topic_export.csv first if not empty
        if os.path.exists(topic_path) and os.path.getsize(topic_path) > 0:
            with open(topic_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    topic_id = row.get('id', '').strip()
                    course_id = row.get('course_id', '').strip()
                    title = row.get('title', '').strip()
                    if not title or not course_id:
                        continue
                    course = Course.objects.filter(id=course_id).first()
                    if course:
                        topic, created = Topic.objects.update_or_create(
                            id=topic_id if topic_id else None,
                            defaults={
                                'course': course,
                                'title': title,
                                'description': row.get('description', '').strip(),
                                'is_active': row.get('is_active', 'true').lower() == 'true',
                            }
                        )
                        if created:
                            created_count += 1
                        count += 1

        # Fallback / Supplement: Extract topics from Question_export.csv
        if os.path.exists(question_path):
            self.stdout.write(self.style.SUCCESS("Extracting topic metadata from Question_export.csv..."))
            with open(question_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    topic_id = row.get('topic_id', '').strip()
                    topic_title = row.get('topic_title', '').strip()
                    course_id = row.get('course_id', '').strip()

                    if topic_id and topic_title and course_id:
                        course = Course.objects.filter(id=course_id).first()
                        if course:
                            topic, created = Topic.objects.update_or_create(
                                id=topic_id,
                                defaults={
                                    'course': course,
                                    'title': topic_title,
                                    'is_active': True,
                                }
                            )
                            if created:
                                created_count += 1
                            count += 1

        self.stdout.write(self.style.SUCCESS(f"Topics import finished! Processed: {count}, Created: {created_count}"))
