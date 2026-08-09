import os
import csv
import json
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.contrib.auth import get_user_model

from departments.models import Department
from courses.models import Course
from topics.models import Topic
from questions.models import Question
from students.models import StudentProfile
from activation_codes.models import ActivationCode
from practice.models import PracticeSession, PracticeAttempt
from results.models import MockExamResult
from bookmarks.models import Bookmark
from referrals.models import Referral, WithdrawalRequest

logger = logging.getLogger(__name__)
User = get_user_model()

def parse_dt(val):
    if not val or not str(val).strip():
        return None
    val_str = str(val).strip()
    dt = parse_datetime(val_str)
    if dt:
        return dt
    try:
        return datetime.fromisoformat(val_str.replace('Z', '+00:00'))
    except Exception:
        return None

def parse_bool(val):
    if isinstance(val, bool):
        return val
    if not val:
        return False
    return str(val).strip().lower() in ('true', '1', 't', 'yes')

def parse_int(val, default=0):
    if val is None or str(val).strip() == '':
        return default
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return default

def parse_float(val, default=0.0):
    if val is None or str(val).strip() == '':
        return default
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return default

def parse_json(val, default=None):
    if default is None:
        default = {}
    if not val or not str(val).strip():
        return default
    try:
        return json.loads(val)
    except Exception:
        return default

class Command(BaseCommand):
    help = "Imports CSV exported data into Django models atomically with validation and detailed report."

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '..', 'baackend data'),
            help='Directory containing CSV export files'
        )

    def handle(self, *args, **options):
        data_dir = os.path.abspath(options.get('data_dir') or options.get('data-dir'))
        self.stdout.write(self.style.NOTICE(f"Starting CSV import from directory: {data_dir}"))

        report = {
            'users': {'imported': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'departments': {'imported': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'courses': {'imported': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'topics': {'imported': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'questions': {'imported': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'activation_codes': {'imported': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'student_profiles': {'imported': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'practice_sessions': {'imported': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'practice_attempts': {'imported': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'mock_exam_results': {'imported': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'bookmarks': {'imported': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'referrals': {'imported': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'withdrawal_requests': {'imported': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
        }

        try:
            with transaction.atomic():
                self.import_users(data_dir, report['users'])
                self.import_departments(data_dir, report['departments'])
                self.import_courses(data_dir, report['courses'])
                self.import_topics(data_dir, report['topics'])
                self.import_questions(data_dir, report['questions'])
                self.import_activation_codes(data_dir, report['activation_codes'])
                self.import_student_profiles(data_dir, report['student_profiles'])

                # Build user_id_map: old MongoDB user_id -> Django User object
                # (reads StudentProfile CSV which has both user_id and email)
                user_id_map = self.build_user_id_map(data_dir)
                self.stdout.write(self.style.NOTICE(f"  Built user_id_map with {len(user_id_map)} entries."))

                self.import_practice_sessions(data_dir, report['practice_sessions'], user_id_map)
                self.import_practice_attempts(data_dir, report['practice_attempts'], user_id_map)
                self.import_mock_exam_results(data_dir, report['mock_exam_results'], user_id_map)
                self.import_bookmarks(data_dir, report['bookmarks'], user_id_map)
                self.import_referrals(data_dir, report['referrals'], user_id_map)
                self.import_withdrawal_requests(data_dir, report['withdrawal_requests'], user_id_map)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Fatal error during CSV import: {e}"))
            raise e

        self.stdout.write(self.style.SUCCESS("\n=== CSV Import Final Summary Report ==="))
        for model_name, stats in report.items():
            self.stdout.write(
                f"{model_name.upper():<22} | Created: {stats['imported']:<5} | Updated: {stats['updated']:<5} | Skipped: {stats['skipped']:<5} | Errors: {stats['errors']:<5}"
            )
        self.stdout.write(self.style.SUCCESS("=======================================\n"))

    def find_csv(self, data_dir, *possible_names):
        for name in possible_names:
            path = os.path.join(data_dir, name)
            if os.path.exists(path):
                return path
        return None

    def build_user_id_map(self, data_dir):
        """
        Build a mapping from old MongoDB user_id -> Django User object.
        Uses StudentProfile CSV which contains both old user_id and email.
        Falls back to User table lookup by email.
        """
        user_id_map = {}
        filepath = self.find_csv(data_dir, 'StudentProfile_export.csv')
        if not filepath:
            return user_id_map

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                old_user_id = row.get('user_id', '').strip()
                email = row.get('email', '').strip()
                if not old_user_id:
                    continue

                # Try Django User by id first (in case it was preserved), then by email
                user = User.objects.filter(id=old_user_id).first()
                if not user and email:
                    user = User.objects.filter(email=email).first()

                if user:
                    user_id_map[old_user_id] = user

        # Also map activation code student ids from ActivationCode CSV
        act_filepath = self.find_csv(data_dir, 'ActivationCode_export (1).csv', 'ActivationCode_export.csv')
        if act_filepath:
            with open(act_filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    student_id = row.get('assigned_student_id', '').strip()
                    email = row.get('assigned_student_email', '').strip()
                    if student_id and student_id not in user_id_map:
                        user = User.objects.filter(id=student_id).first()
                        if not user and email:
                            user = User.objects.filter(email=email).first()
                        if user:
                            user_id_map[student_id] = user

        return user_id_map

    def import_users(self, data_dir, stats):
        filepath = self.find_csv(data_dir, 'mystudyapp-users.csv')
        if not filepath:
            self.stdout.write(self.style.WARNING("Users CSV file not found."))
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row.get('email', '').strip()
                if not email:
                    stats['skipped'] += 1
                    continue
                role_val = row.get('role', 'user').strip()
                if role_val not in dict(User.Role.choices):
                    role_val = User.Role.STUDENT
                status_val = row.get('status', 'active').strip()
                if status_val not in dict(User.Status.choices):
                    status_val = User.Status.ACTIVE

                user, created = User.objects.update_or_create(
                    email=email,
                    defaults={
                        'full_name': row.get('full_name', '').strip(),
                        'role': role_val,
                        'status': status_val,
                    }
                )
                if created:
                    user.set_unusable_password()
                    user.save()
                    stats['imported'] += 1
                else:
                    stats['updated'] += 1

    def import_departments(self, data_dir, stats):
        filepath = self.find_csv(data_dir, 'Department_export.csv')
        if not filepath:
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                dep_id = row.get('id', '').strip()
                name = row.get('name', '').strip()
                if not name or not dep_id:
                    stats['skipped'] += 1
                    continue
                levels_json = parse_json(row.get('levels'), default=['100'])
                dept, created = Department.objects.update_or_create(
                    id=dep_id,
                    defaults={
                        'name': name,
                        'description': row.get('description', '').strip(),
                        'is_active': parse_bool(row.get('is_active', 'true')),
                        'levels': levels_json,
                    }
                )
                if created:
                    stats['imported'] += 1
                else:
                    stats['updated'] += 1

    def import_courses(self, data_dir, stats):
        filepath = self.find_csv(data_dir, 'Course_export.csv', 'Course_export (1).csv')
        if not filepath:
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                course_id = row.get('id', '').strip()
                code = row.get('code', '').strip()
                if not course_id or not code:
                    stats['skipped'] += 1
                    continue
                dept_id = row.get('department_id', '').strip()
                dept = Department.objects.filter(id=dept_id).first() if dept_id else None

                course, created = Course.objects.update_or_create(
                    id=course_id,
                    defaults={
                        'department': dept,
                        'department_name': row.get('department_name', '').strip(),
                        'title': row.get('title', '').strip(),
                        'code': code,
                        'level': row.get('level', '100').strip(),
                        'description': row.get('description', '').strip(),
                        'icon': row.get('icon', '').strip(),
                        'is_active': parse_bool(row.get('is_active', 'true')),
                        'question_count': parse_int(row.get('question_count'), 0),
                    }
                )
                if created:
                    stats['imported'] += 1
                else:
                    stats['updated'] += 1

    def import_topics(self, data_dir, stats):
        filepath = self.find_csv(data_dir, 'Topic_export.csv')
        if not filepath:
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                topic_id = row.get('id', '').strip()
                title = row.get('title', '').strip()
                course_id = row.get('course_id', '').strip()
                if not topic_id or not title or not course_id:
                    stats['skipped'] += 1
                    continue
                course = Course.objects.filter(id=course_id).first()
                if not course:
                    stats['skipped'] += 1
                    continue

                topic, created = Topic.objects.update_or_create(
                    id=topic_id,
                    defaults={
                        'course': course,
                        'title': title,
                        'description': row.get('description', '').strip(),
                        'is_active': parse_bool(row.get('is_active', 'true')),
                    }
                )
                if created:
                    stats['imported'] += 1
                else:
                    stats['updated'] += 1

    def import_questions(self, data_dir, stats):
        filepath = self.find_csv(data_dir, 'Question_export.csv')
        if not filepath:
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                q_id = row.get('id', '').strip()
                course_id = row.get('course_id', '').strip()
                if not q_id or not course_id:
                    stats['skipped'] += 1
                    continue
                course = Course.objects.filter(id=course_id).first()
                if not course:
                    stats['skipped'] += 1
                    continue

                topic_id = row.get('topic_id', '').strip()
                topic = Topic.objects.filter(id=topic_id).first() if topic_id else None

                corr = row.get('correct_answer', 'A').strip().upper()
                if corr not in ('A', 'B', 'C', 'D'):
                    corr = 'A'

                diff = row.get('difficulty', 'medium').strip().lower()
                if diff not in ('easy', 'medium', 'hard'):
                    diff = 'medium'

                question, created = Question.objects.update_or_create(
                    id=q_id,
                    defaults={
                        'course': course,
                        'topic': topic,
                        'topic_title': row.get('topic_title', '').strip(),
                        'course_code': row.get('course_code', course.code).strip(),
                        'question_text': row.get('question_text', '').strip(),
                        'option_a': row.get('option_a', '').strip(),
                        'option_b': row.get('option_b', '').strip(),
                        'option_c': row.get('option_c', '').strip(),
                        'option_d': row.get('option_d', '').strip(),
                        'correct_answer': corr,
                        'explanation': row.get('explanation', '').strip(),
                        'difficulty': diff,
                        'is_active': parse_bool(row.get('is_active', 'true')),
                        'is_free_trial': parse_bool(row.get('is_free_trial', 'false')),
                    }
                )
                if created:
                    stats['imported'] += 1
                else:
                    stats['updated'] += 1

    def import_activation_codes(self, data_dir, stats):
        filepath = self.find_csv(data_dir, 'ActivationCode_export (1).csv', 'ActivationCode_export.csv')
        if not filepath:
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code_id = row.get('id', '').strip()
                code_str = row.get('code', '').strip()
                if not code_id or not code_str:
                    stats['skipped'] += 1
                    continue

                student_id = row.get('assigned_student_id', '').strip()
                student_user = User.objects.filter(id=student_id).first() if student_id else None
                if not student_user and row.get('assigned_student_email'):
                    student_user = User.objects.filter(email=row.get('assigned_student_email').strip()).first()

                code_obj, created = ActivationCode.objects.update_or_create(
                    id=code_id,
                    defaults={
                        'code': code_str,
                        'access_duration': row.get('access_duration', 'full_time').strip(),
                        'status': row.get('status', 'unused').strip(),
                        'notes': row.get('notes', '').strip(),
                        'assigned_student': student_user,
                        'assigned_student_email': row.get('assigned_student_email', '').strip(),
                        'assigned_student_name': row.get('assigned_student_name', '').strip(),
                        'date_activated': parse_dt(row.get('date_activated')),
                        'is_sample': parse_bool(row.get('is_sample', 'false')),
                    }
                )
                if created:
                    stats['imported'] += 1
                else:
                    stats['updated'] += 1

    def import_student_profiles(self, data_dir, stats):
        filepath = self.find_csv(data_dir, 'StudentProfile_export.csv')
        if not filepath:
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prof_id = row.get('id', '').strip()
                user_id = row.get('user_id', '').strip()
                email = row.get('email', '').strip()
                if not prof_id:
                    stats['skipped'] += 1
                    continue

                user = User.objects.filter(id=user_id).first() if user_id else None
                if not user and email:
                    user = User.objects.filter(email=email).first()

                if not user:
                    user = User.objects.create_user(
                        email=email or f"user_{prof_id}@mystudyapp.com",
                        full_name=row.get('full_name', '').strip(),
                        role=User.Role.STUDENT
                    )

                dept_id = row.get('department_id', '').strip()
                dept = Department.objects.filter(id=dept_id).first() if dept_id else None
                free_trial_json = parse_json(row.get('free_trial_used'), default={})

                profile, created = StudentProfile.objects.update_or_create(
                    id=prof_id,
                    defaults={
                        'user': user,
                        'department': dept,
                        'department_name': row.get('department_name', '').strip(),
                        'level': row.get('level', '100').strip(),
                        'full_name': row.get('full_name', '').strip(),
                        'email': email or user.email,
                        'profile_image': row.get('profile_image', '').strip(),
                        'my_referral_code': row.get('my_referral_code', '').strip(),
                        'referral_code': row.get('referral_code', '').strip(),
                        'is_activated': parse_bool(row.get('is_activated', 'false')),
                        'activation_code': row.get('activation_code', '').strip(),
                        'activation_date': parse_dt(row.get('activation_date')),
                        'access_expires': parse_dt(row.get('access_expires')),
                        'free_trial_used': free_trial_json,
                        'total_questions_answered': parse_int(row.get('total_questions_answered'), 0),
                        'total_correct': parse_int(row.get('total_correct'), 0),
                        'total_practice_sessions': parse_int(row.get('total_practice_sessions'), 0),
                        'total_mock_exams': parse_int(row.get('total_mock_exams'), 0),
                    }
                )
                if created:
                    stats['imported'] += 1
                else:
                    stats['updated'] += 1

    def import_practice_sessions(self, data_dir, stats, user_id_map=None):
        if user_id_map is None:
            user_id_map = {}
        filepath = self.find_csv(data_dir, 'PracticeSession_export.csv')
        if not filepath:
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ps_id = row.get('id', '').strip()
                user_id = row.get('user_id', '').strip()
                course_id = row.get('course_id', '').strip()
                if not ps_id or not user_id or not course_id:
                    stats['skipped'] += 1
                    continue
                # Use map first, fall back to direct DB lookup
                user = user_id_map.get(user_id) or User.objects.filter(id=user_id).first()
                course = Course.objects.filter(id=course_id).first()
                if not user or not course:
                    stats['skipped'] += 1
                    continue

                topic_id = row.get('topic_id', '').strip()
                topic = Topic.objects.filter(id=topic_id).first() if topic_id else None

                session, created = PracticeSession.objects.update_or_create(
                    id=ps_id,
                    defaults={
                        'user': user,
                        'course': course,
                        'topic': topic,
                        'course_code': row.get('course_code', course.code).strip(),
                        'mode': row.get('mode', 'practice').strip(),
                        'total_questions': parse_int(row.get('total_questions'), 0),
                        'correct_answers': parse_int(row.get('correct_answers'), 0),
                        'wrong_answers': parse_int(row.get('wrong_answers'), 0),
                        'score_percentage': parse_float(row.get('score_percentage'), 0.0),
                    }
                )
                if created:
                    stats['imported'] += 1
                else:
                    stats['updated'] += 1

    def import_practice_attempts(self, data_dir, stats, user_id_map=None):
        if user_id_map is None:
            user_id_map = {}
        filepath = self.find_csv(data_dir, 'PracticeAttempt_export.csv')
        if not filepath:
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pa_id = row.get('id', '').strip()
                user_id = row.get('user_id', '').strip()
                course_id = row.get('course_id', '').strip()
                if not pa_id or not user_id or not course_id:
                    stats['skipped'] += 1
                    continue
                user = user_id_map.get(user_id) or User.objects.filter(id=user_id).first()
                course = Course.objects.filter(id=course_id).first()
                if not user or not course:
                    stats['skipped'] += 1
                    continue

                topic_id = row.get('topic_id', '').strip()
                topic = Topic.objects.filter(id=topic_id).first() if topic_id else None

                q_id = row.get('question_id', '').strip()
                question = Question.objects.filter(id=q_id).first() if q_id else None

                attempt, created = PracticeAttempt.objects.update_or_create(
                    id=pa_id,
                    defaults={
                        'user': user,
                        'course': course,
                        'topic': topic,
                        'question': question,
                        'course_code': row.get('course_code', course.code).strip(),
                        'selected_answer': row.get('selected_answer', '').strip(),
                        'correct_answer': row.get('correct_answer', '').strip(),
                        'is_correct': parse_bool(row.get('is_correct', 'false')),
                        'time_spent_seconds': parse_int(row.get('time_spent_seconds'), 0),
                        'mode': row.get('mode', 'practice').strip(),
                    }
                )
                if created:
                    stats['imported'] += 1
                else:
                    stats['updated'] += 1

    def import_mock_exam_results(self, data_dir, stats, user_id_map=None):
        if user_id_map is None:
            user_id_map = {}
        filepath = self.find_csv(data_dir, 'MockExamResult_export.csv')
        if not filepath:
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                me_id = row.get('id', '').strip()
                user_id = row.get('user_id', '').strip()
                course_id = row.get('course_id', '').strip()
                if not me_id or not user_id or not course_id:
                    stats['skipped'] += 1
                    continue
                user = user_id_map.get(user_id) or User.objects.filter(id=user_id).first()
                course = Course.objects.filter(id=course_id).first()
                if not user or not course:
                    stats['skipped'] += 1
                    continue

                answers_json = parse_json(row.get('answers'), default=[])

                result, created = MockExamResult.objects.update_or_create(
                    id=me_id,
                    defaults={
                        'user': user,
                        'course': course,
                        'course_code': row.get('course_code', course.code).strip(),
                        'total_questions': parse_int(row.get('total_questions'), 0),
                        'correct_answers': parse_int(row.get('correct_answers'), 0),
                        'wrong_answers': parse_int(row.get('wrong_answers'), 0),
                        'unanswered': parse_int(row.get('unanswered'), 0),
                        'score_percentage': parse_float(row.get('score_percentage'), 0.0),
                        'time_spent_seconds': parse_int(row.get('time_spent_seconds'), 0),
                        'time_allowed_seconds': parse_int(row.get('time_allowed_seconds'), 0),
                        'passed': parse_bool(row.get('passed', 'false')),
                        'answers': answers_json,
                    }
                )
                if created:
                    stats['imported'] += 1
                else:
                    stats['updated'] += 1

    def import_bookmarks(self, data_dir, stats, user_id_map=None):
        if user_id_map is None:
            user_id_map = {}
        filepath = self.find_csv(data_dir, 'Bookmark_export (1).csv', 'Bookmark_export.csv')
        if not filepath:
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                bm_id = row.get('id', '').strip()
                user_id = row.get('user_id', '').strip()
                course_id = row.get('course_id', '').strip()
                q_id = row.get('question_id', '').strip()
                if not bm_id or not user_id or not course_id or not q_id:
                    stats['skipped'] += 1
                    continue
                user = user_id_map.get(user_id) or User.objects.filter(id=user_id).first()
                course = Course.objects.filter(id=course_id).first()
                question = Question.objects.filter(id=q_id).first()
                if not user or not course or not question:
                    stats['skipped'] += 1
                    continue

                bm, created = Bookmark.objects.update_or_create(
                    user=user,
                    question=question,
                    defaults={
                        'course': course,
                        'course_code': row.get('course_code', course.code).strip(),
                    }
                )
                if created:
                    stats['imported'] += 1
                else:
                    stats['updated'] += 1

    def import_referrals(self, data_dir, stats, user_id_map=None):
        if user_id_map is None:
            user_id_map = {}
        filepath = self.find_csv(data_dir, 'Referral_export.csv')
        if not filepath:
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ref_id = row.get('id', '').strip()
                referrer_id = row.get('referrer_user_id', '').strip()
                if not ref_id or not referrer_id:
                    stats['skipped'] += 1
                    continue
                referrer = user_id_map.get(referrer_id) or User.objects.filter(id=referrer_id).first()
                if not referrer:
                    stats['skipped'] += 1
                    continue

                referred_id = row.get('referred_user_id', '').strip()
                referred = user_id_map.get(referred_id) if referred_id else None
                if not referred and referred_id:
                    referred = User.objects.filter(id=referred_id).first()

                referral, created = Referral.objects.update_or_create(
                    id=ref_id,
                    defaults={
                        'referrer_user': referrer,
                        'referred_user': referred,
                        'referrer_code': row.get('referrer_code', '').strip(),
                        'referred_email': row.get('referred_email', '').strip(),
                        'referred_name': row.get('referred_name', '').strip(),
                        'reward_amount': parse_float(row.get('reward_amount'), 500.00),
                        'status': row.get('status', 'pending').strip(),
                        'paid_date': parse_dt(row.get('paid_date')),
                    }
                )
                if created:
                    stats['imported'] += 1
                else:
                    stats['updated'] += 1

    def import_withdrawal_requests(self, data_dir, stats, user_id_map=None):
        if user_id_map is None:
            user_id_map = {}
        filepath = self.find_csv(data_dir, 'WithdrawalRequest_export.csv')
        if not filepath:
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                wr_id = row.get('id', '').strip()
                user_id = row.get('user_id', '').strip()
                if not wr_id or not user_id:
                    stats['skipped'] += 1
                    continue
                user = user_id_map.get(user_id) or User.objects.filter(id=user_id).first()
                if not user:
                    stats['skipped'] += 1
                    continue

                wr, created = WithdrawalRequest.objects.update_or_create(
                    id=wr_id,
                    defaults={
                        'user': user,
                        'referral_code': row.get('referral_code', '').strip(),
                        'full_name': row.get('full_name', '').strip(),
                        'email': row.get('email', user.email).strip(),
                        'bank_name': row.get('bank_name', '').strip(),
                        'account_number': row.get('account_number', '').strip(),
                        'account_name': row.get('account_name', '').strip(),
                        'amount': parse_float(row.get('amount'), 0.0),
                        'status': row.get('status', 'pending').strip(),
                        'paid_date': parse_dt(row.get('paid_date')),
                    }
                )
                if created:
                    stats['imported'] += 1
                else:
                    stats['updated'] += 1

