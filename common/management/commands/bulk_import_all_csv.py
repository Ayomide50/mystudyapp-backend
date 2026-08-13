"""Fast, transactional importer for the legacy CSV export directory.

This command is deliberately intended for an empty target database.  It keeps
the legacy primary keys used by the exports, validates foreign-key references
before writing, then uses Django bulk operations so large exports do not time
out over a hosted PostgreSQL connection.
"""

import csv
import hashlib
import json
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from activation_codes.models import ActivationCode
from bookmarks.models import Bookmark
from courses.models import Course
from departments.models import Department
from practice.models import PracticeAttempt, PracticeSession
from questions.models import Question
from referrals.models import Referral, WithdrawalRequest
from results.models import MockExamResult
from students.models import StudentProfile
from topics.models import Topic


User = get_user_model()
BATCH_SIZE = 500


def value(row, key, default=""):
    return (row.get(key) or default).strip()


def parse_bool(raw, default=False):
    if raw is None or not str(raw).strip():
        return default
    return str(raw).strip().lower() in {"1", "true", "t", "yes"}


def parse_int(raw, default=0):
    try:
        return int(float(raw)) if str(raw).strip() else default
    except (TypeError, ValueError):
        return default


def parse_float(raw, default=0.0):
    try:
        return float(raw) if str(raw).strip() else default
    except (TypeError, ValueError):
        return default


def parse_decimal(raw, default="0"):
    try:
        return Decimal(str(raw).strip()) if str(raw).strip() else Decimal(default)
    except (InvalidOperation, ValueError):
        return Decimal(default)


def parse_json(raw, default):
    if raw is None or not str(raw).strip():
        return default
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return default


def parse_dt(raw):
    if raw is None or not str(raw).strip():
        return None
    raw = str(raw).strip()
    parsed = parse_datetime(raw) or _iso_dt(raw)
    if parsed and timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _iso_dt(raw):
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


class Command(BaseCommand):
    help = "Bulk-imports the legacy CSV export into an empty Django database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-dir",
            default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "..", "baackend data"),
            help="Directory containing the CSV export files.",
        )

    def handle(self, *args, **options):
        self.data_dir = os.path.abspath(options["data_dir"])
        if not os.path.isdir(self.data_dir):
            raise CommandError(f"CSV directory does not exist: {self.data_dir}")

        self.import_notes = {}
        self.assert_empty_target()
        self.rows = {name: self.read_csv(filename) for name, filename in self.files().items()}
        self.validate_ids()

        with transaction.atomic():
            self.import_all()

        self.stdout.write(self.style.SUCCESS("Bulk CSV import completed successfully."))
        for name, count in self.counts.items():
            self.stdout.write(f"{name}: {count}")
        for note, count in self.import_notes.items():
            self.stdout.write(self.style.WARNING(f"{note}: {count}"))

    def note_import_repair(self, note, count=1):
        self.import_notes[note] = self.import_notes.get(note, 0) + count

    @staticmethod
    def files():
        return {
            "users": "mystudyapp-users.csv",
            "departments": "Department_export.csv",
            "courses": "Course_export.csv",
            "topics": "Topic_export.csv",
            "questions": "Question_export.csv",
            "activation_codes": "ActivationCode_export.csv",
            "student_profiles": "StudentProfile_export.csv",
            "practice_sessions": "PracticeSession_export.csv",
            "practice_attempts": "PracticeAttempt_export.csv",
            "mock_exam_results": "MockExamResult_export.csv",
            "bookmarks": "Bookmark_export.csv",
            "referrals": "Referral_export.csv",
            "withdrawal_requests": "WithdrawalRequest_export.csv",
        }

    @staticmethod
    def target_models():
        return (
            User, Department, Course, Topic, Question, ActivationCode,
            StudentProfile, PracticeSession, PracticeAttempt, MockExamResult,
            Bookmark, Referral, WithdrawalRequest,
        )

    def assert_empty_target(self):
        populated = [model._meta.label for model in self.target_models() if model.objects.exists()]
        if populated:
            raise CommandError(
                "The target database is not empty; refusing to mix a legacy bulk import "
                f"with existing records: {', '.join(populated)}"
            )

    def read_csv(self, filename):
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return []
        with open(path, newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))

    def validate_ids(self):
        for name, rows in self.rows.items():
            if name == "users":
                continue
            seen = set()
            for row in rows:
                record_id = value(row, "id")
                if not record_id:
                    raise CommandError(f"{name} contains a row without an id.")
                if record_id in seen:
                    raise CommandError(f"{name} contains duplicate id {record_id!r}.")
                seen.add(record_id)

        emails = [value(row, "email").lower() for row in self.rows["users"] if value(row, "email")]
        if len(emails) != len(set(emails)):
            raise CommandError("The users export contains duplicate email addresses.")

    def bulk_insert(self, label, objects, audit):
        if not objects:
            self.counts[label] = 0
            return
        objects[0].__class__.objects.bulk_create(objects, batch_size=BATCH_SIZE)
        timestamped = []
        for obj, created_at, updated_at in audit:
            if created_at:
                obj.created_at = created_at
            if updated_at:
                obj.updated_at = updated_at
            timestamped.append(obj)
        if timestamped:
            objects[0].__class__.objects.bulk_update(
                timestamped, ["created_at", "updated_at"], batch_size=BATCH_SIZE
            )
        self.counts[label] = len(objects)

    @staticmethod
    def audit_values(row):
        return parse_dt(row.get("created_date")), parse_dt(row.get("updated_date"))

    def import_all(self):
        self.counts = {}
        imports = (
            ("users", self.import_users),
            ("departments", self.import_departments),
            ("courses", self.import_courses),
            ("topics", self.import_topics),
            ("questions", self.import_questions),
            ("activation_codes", self.import_activation_codes),
            ("student_profiles", self.import_profiles),
            ("practice_sessions", self.import_practice_sessions),
            ("practice_attempts", self.import_practice_attempts),
            ("mock_exam_results", self.import_mock_exam_results),
            ("bookmarks", self.import_bookmarks),
            ("referrals", self.import_referrals),
            ("withdrawal_requests", self.import_withdrawals),
        )
        for label, import_records in imports:
            import_records()
            self.stdout.write(f"Prepared {self.counts[label]} {label} record(s).")

    def import_users(self):
        required_legacy_users = {}

        def add_required_user(legacy_id, email="", full_name=""):
            if not legacy_id:
                return
            details = required_legacy_users.setdefault(
                legacy_id, {"email": "", "full_name": ""}
            )
            if email and not details["email"]:
                details["email"] = email.lower()
            if full_name and not details["full_name"]:
                details["full_name"] = full_name

        for row in self.rows["student_profiles"]:
            add_required_user(value(row, "user_id"), value(row, "email"), value(row, "full_name"))
        for row in self.rows["practice_sessions"]:
            add_required_user(value(row, "user_id"))
        for row in self.rows["practice_attempts"]:
            add_required_user(value(row, "user_id"))
        for row in self.rows["mock_exam_results"]:
            add_required_user(value(row, "user_id"))
        for row in self.rows["bookmarks"]:
            add_required_user(value(row, "user_id"))
        for row in self.rows["referrals"]:
            add_required_user(value(row, "referrer_user_id"))
            add_required_user(
                value(row, "referred_user_id"), value(row, "referred_email"), value(row, "referred_name")
            )
        for row in self.rows["withdrawal_requests"]:
            add_required_user(value(row, "user_id"), value(row, "email"), value(row, "full_name"))
        for row in self.rows["activation_codes"]:
            add_required_user(
                value(row, "assigned_student_id"),
                value(row, "assigned_student_email"),
                value(row, "assigned_student_name"),
            )

        profiles_by_email = {}
        for row in self.rows["student_profiles"]:
            email = value(row, "email").lower()
            old_id = value(row, "user_id")
            if not email or not old_id:
                raise CommandError("Every student profile requires both email and user_id.")
            if email in profiles_by_email and profiles_by_email[email] != old_id:
                raise CommandError(f"Multiple legacy user IDs exist for {email!r}.")
            profiles_by_email[email] = old_id

        source_by_email = {value(row, "email").lower(): row for row in self.rows["users"] if value(row, "email")}
        source_by_email.update({
            email: {"email": email, "full_name": value(row, "full_name"), "role": "user", "status": "active"}
            for email, row in ((value(row, "email").lower(), row) for row in self.rows["student_profiles"])
            if email and email not in source_by_email
        })

        objects, audit = [], []
        valid_roles = set(User.Role.values)
        valid_statuses = set(User.Status.values)
        self.user_ids_by_email = {}
        self.user_ids_by_legacy_id = {}
        for email, row in source_by_email.items():
            user_id = profiles_by_email.get(email)
            if not user_id:
                user_id = hashlib.sha256(f"mystudyapp:user:{email}".encode()).hexdigest()[:64]
            role = value(row, "role", User.Role.STUDENT)
            status = value(row, "status", User.Status.ACTIVE)
            obj = User(
                id=user_id, email=email, username=email, full_name=value(row, "full_name"),
                role=role if role in valid_roles else User.Role.STUDENT,
                status=status if status in valid_statuses else User.Status.ACTIVE,
                password="!",
            )
            objects.append(obj)
            audit.append((obj, *self.audit_values(row)))
            self.user_ids_by_email[email] = user_id
            if email in profiles_by_email:
                self.user_ids_by_legacy_id[profiles_by_email[email]] = user_id

        # Some older activity records refer to accounts that were no longer
        # present in the profile export. Retain that activity with a disabled
        # migration-only account instead of dropping the related records.
        for legacy_id, details in required_legacy_users.items():
            if legacy_id in self.user_ids_by_legacy_id:
                continue

            email = details["email"]
            existing_user_id = self.user_ids_by_email.get(email) if email else None
            if existing_user_id:
                self.user_ids_by_legacy_id[legacy_id] = existing_user_id
                continue

            email = email or f"legacy-{legacy_id.lower()}@mystudyapp.invalid"
            obj = User(
                id=legacy_id,
                email=email,
                username=email,
                full_name=details["full_name"],
                role=User.Role.STUDENT,
                status=User.Status.INACTIVE,
                password="!",
            )
            objects.append(obj)
            audit.append((obj, None, None))
            self.user_ids_by_email[email] = legacy_id
            self.user_ids_by_legacy_id[legacy_id] = legacy_id
            self.note_import_repair("placeholder legacy user accounts created")
        self.bulk_insert("users", objects, audit)

    def import_departments(self):
        objects, audit = [], []
        self.department_ids = set()
        for row in self.rows["departments"]:
            record_id = value(row, "id")
            self.department_ids.add(record_id)
            obj = Department(
                id=record_id, name=value(row, "name"), description=value(row, "description"),
                is_active=parse_bool(row.get("is_active"), True),
                levels=parse_json(row.get("levels"), ["100"]),
            )
            objects.append(obj)
            audit.append((obj, *self.audit_values(row)))
        self.bulk_insert("departments", objects, audit)

    def import_courses(self):
        objects, audit = [], []
        self.course_ids = set()
        for row in self.rows["courses"]:
            record_id = value(row, "id")
            department_id = value(row, "department_id") or None
            if department_id and department_id not in self.department_ids:
                raise CommandError(f"Course {record_id!r} references missing department {department_id!r}.")
            self.course_ids.add(record_id)
            obj = Course(
                id=record_id, department_id=department_id, department_name=value(row, "department_name"),
                title=value(row, "title"), code=value(row, "code"), level=value(row, "level", "100"),
                description=value(row, "description"), icon=value(row, "icon"),
                is_active=parse_bool(row.get("is_active"), True),
                question_count=parse_int(row.get("question_count")),
            )
            objects.append(obj)
            audit.append((obj, *self.audit_values(row)))
        self.bulk_insert("courses", objects, audit)

    def import_topics(self):
        topic_rows = list(self.rows["topics"])
        # The supplied Topic export is empty. Reconstruct topic records from the
        # topic IDs and titles carried by question rows, preserving relationships.
        derived = {}
        for row in self.rows["questions"]:
            record_id = value(row, "topic_id")
            if not record_id:
                continue
            course_id = value(row, "course_id")
            title = value(row, "topic_title") or "Untitled topic"
            previous = derived.get(record_id)
            current = (course_id, title, row)
            if previous and previous[:2] != current[:2]:
                raise CommandError(f"Topic {record_id!r} has conflicting course or title values.")
            derived[record_id] = current
        topic_rows.extend(
            {
                "id": record_id, "course_id": course_id, "title": title,
                "description": "", "is_active": "true",
                "created_date": row.get("created_date"), "updated_date": row.get("updated_date"),
            }
            for record_id, (course_id, title, row) in derived.items()
        )

        objects, audit = [], []
        self.topic_ids = set()
        for row in topic_rows:
            record_id = value(row, "id")
            course_id = value(row, "course_id")
            if not record_id or not course_id:
                raise CommandError("Every topic requires id and course_id.")
            if course_id not in self.course_ids:
                raise CommandError(f"Topic {record_id!r} references missing course {course_id!r}.")
            self.topic_ids.add(record_id)
            obj = Topic(
                id=record_id, course_id=course_id, title=value(row, "title"),
                description=value(row, "description"), is_active=parse_bool(row.get("is_active"), True),
            )
            objects.append(obj)
            audit.append((obj, *self.audit_values(row)))
        self.bulk_insert("topics", objects, audit)

    def import_questions(self):
        objects, audit = [], []
        self.question_ids = set()
        valid_difficulties = set(Question.Difficulty.values)
        valid_answers = set(Question.CorrectAnswer.values)
        for row in self.rows["questions"]:
            record_id = value(row, "id")
            course_id = value(row, "course_id")
            topic_id = value(row, "topic_id") or None
            if course_id not in self.course_ids:
                raise CommandError(f"Question {record_id!r} references missing course {course_id!r}.")
            if topic_id and topic_id not in self.topic_ids:
                topic_id = None
            difficulty = value(row, "difficulty", Question.Difficulty.MEDIUM).lower()
            correct_answer = value(row, "correct_answer", Question.CorrectAnswer.A).upper()
            self.question_ids.add(record_id)
            obj = Question(
                id=record_id, course_id=course_id, topic_id=topic_id,
                topic_title=value(row, "topic_title"), course_code=value(row, "course_code"),
                question_text=value(row, "question_text"), option_a=value(row, "option_a"),
                option_b=value(row, "option_b"), option_c=value(row, "option_c"), option_d=value(row, "option_d"),
                correct_answer=correct_answer if correct_answer in valid_answers else Question.CorrectAnswer.A,
                explanation=value(row, "explanation"),
                difficulty=difficulty if difficulty in valid_difficulties else Question.Difficulty.MEDIUM,
                is_active=parse_bool(row.get("is_active"), True),
                is_free_trial=parse_bool(row.get("is_free_trial")),
            )
            objects.append(obj)
            audit.append((obj, *self.audit_values(row)))

        # A small number of attempts and bookmarks reference questions that
        # were removed before the question export was created. Keep those
        # historical records usable by creating inactive placeholder questions.
        missing_question_sources = {}
        for source_name in ("practice_attempts", "bookmarks"):
            for row in self.rows[source_name]:
                record_id = value(row, "question_id")
                if not record_id or record_id in self.question_ids:
                    continue
                course_id = value(row, "course_id")
                if course_id not in self.course_ids:
                    raise CommandError(
                        f"Missing question {record_id!r} references missing course {course_id!r}."
                    )
                previous = missing_question_sources.get(record_id)
                if previous and value(previous, "course_id") != course_id:
                    raise CommandError(
                        f"Missing question {record_id!r} has conflicting course references."
                    )
                if not previous or value(row, "question_text"):
                    missing_question_sources[record_id] = row

        for record_id, row in missing_question_sources.items():
            topic_id = value(row, "topic_id") or None
            correct_answer = value(row, "correct_answer", Question.CorrectAnswer.A).upper()
            obj = Question(
                id=record_id,
                course_id=value(row, "course_id"),
                topic_id=topic_id if topic_id in self.topic_ids else None,
                topic_title=value(row, "topic_title"),
                course_code=value(row, "course_code"),
                question_text=value(row, "question_text") or "Legacy question unavailable in export.",
                option_a=value(row, "option_a"),
                option_b=value(row, "option_b"),
                option_c=value(row, "option_c"),
                option_d=value(row, "option_d"),
                correct_answer=correct_answer if correct_answer in valid_answers else Question.CorrectAnswer.A,
                explanation=value(row, "explanation"),
                difficulty=Question.Difficulty.MEDIUM,
                is_active=False,
                is_free_trial=False,
            )
            self.question_ids.add(record_id)
            objects.append(obj)
            audit.append((obj, *self.audit_values(row)))
            self.note_import_repair("inactive placeholder questions created")
        self.bulk_insert("questions", objects, audit)

    def user_id(self, legacy_id, email=""):
        user_id = self.user_ids_by_legacy_id.get(legacy_id)
        if not user_id and email:
            user_id = self.user_ids_by_email.get(email.lower())
        if not user_id:
            raise CommandError(f"Legacy user {legacy_id!r} cannot be mapped to an imported user.")
        return user_id

    def import_activation_codes(self):
        objects, audit = [], []
        for row in self.rows["activation_codes"]:
            legacy_id = value(row, "assigned_student_id")
            email = value(row, "assigned_student_email")
            assigned_student_id = self.user_id(legacy_id, email) if legacy_id or email else None
            obj = ActivationCode(
                id=value(row, "id"), code=value(row, "code"),
                access_duration=value(row, "access_duration", ActivationCode.Duration.FULL_TIME),
                status=value(row, "status", ActivationCode.Status.UNUSED), notes=value(row, "notes"),
                assigned_student_id=assigned_student_id, assigned_student_email=email,
                assigned_student_name=value(row, "assigned_student_name"),
                date_activated=parse_dt(row.get("date_activated")),
                is_sample=parse_bool(row.get("is_sample")),
            )
            objects.append(obj)
            audit.append((obj, *self.audit_values(row)))
        self.bulk_insert("activation_codes", objects, audit)

    def import_profiles(self):
        objects, audit = [], []
        for row in self.rows["student_profiles"]:
            department_id = value(row, "department_id") or None
            if department_id and department_id not in self.department_ids:
                department_id = None
                self.note_import_repair("profiles retained without a missing department")
            obj = StudentProfile(
                id=value(row, "id"), user_id=self.user_id(value(row, "user_id"), value(row, "email")),
                department_id=department_id, department_name=value(row, "department_name"),
                level=value(row, "level", "100"), full_name=value(row, "full_name"),
                email=value(row, "email"), profile_image=value(row, "profile_image"),
                my_referral_code=value(row, "my_referral_code"), referral_code=value(row, "referral_code"),
                is_activated=parse_bool(row.get("is_activated")), activation_code=value(row, "activation_code"),
                activation_date=parse_dt(row.get("activation_date")), access_expires=parse_dt(row.get("access_expires")),
                free_trial_used=parse_json(row.get("free_trial_used"), {}),
                total_questions_answered=parse_int(row.get("total_questions_answered")),
                total_correct=parse_int(row.get("total_correct")),
                total_practice_sessions=parse_int(row.get("total_practice_sessions")),
                total_mock_exams=parse_int(row.get("total_mock_exams")),
            )
            objects.append(obj)
            audit.append((obj, *self.audit_values(row)))
        self.bulk_insert("student_profiles", objects, audit)

    def import_practice_sessions(self):
        objects, audit = [], []
        for row in self.rows["practice_sessions"]:
            course_id = value(row, "course_id")
            if course_id not in self.course_ids:
                raise CommandError(f"Practice session {value(row, 'id')!r} references a missing course.")
            topic_id = value(row, "topic_id") or None
            obj = PracticeSession(
                id=value(row, "id"), user_id=self.user_id(value(row, "user_id")), course_id=course_id,
                topic_id=topic_id if topic_id in self.topic_ids else None,
                course_code=value(row, "course_code"), mode=value(row, "mode", "practice"),
                total_questions=parse_int(row.get("total_questions")), correct_answers=parse_int(row.get("correct_answers")),
                wrong_answers=parse_int(row.get("wrong_answers")), score_percentage=parse_float(row.get("score_percentage")),
            )
            objects.append(obj)
            audit.append((obj, *self.audit_values(row)))
        self.bulk_insert("practice_sessions", objects, audit)

    def import_practice_attempts(self):
        objects, audit = [], []
        for row in self.rows["practice_attempts"]:
            course_id = value(row, "course_id")
            if course_id not in self.course_ids:
                raise CommandError(f"Practice attempt {value(row, 'id')!r} references a missing course.")
            topic_id = value(row, "topic_id") or None
            question_id = value(row, "question_id") or None
            if question_id and question_id not in self.question_ids:
                raise CommandError(f"Practice attempt {value(row, 'id')!r} references a missing question.")
            obj = PracticeAttempt(
                id=value(row, "id"), user_id=self.user_id(value(row, "user_id")), course_id=course_id,
                topic_id=topic_id if topic_id in self.topic_ids else None, question_id=question_id,
                course_code=value(row, "course_code"), selected_answer=value(row, "selected_answer"),
                correct_answer=value(row, "correct_answer"), is_correct=parse_bool(row.get("is_correct")),
                time_spent_seconds=parse_int(row.get("time_spent_seconds")), mode=value(row, "mode", "practice"),
            )
            objects.append(obj)
            audit.append((obj, *self.audit_values(row)))
        self.bulk_insert("practice_attempts", objects, audit)

    def import_mock_exam_results(self):
        objects, audit = [], []
        for row in self.rows["mock_exam_results"]:
            course_id = value(row, "course_id")
            if course_id not in self.course_ids:
                raise CommandError(f"Mock exam {value(row, 'id')!r} references a missing course.")
            obj = MockExamResult(
                id=value(row, "id"), user_id=self.user_id(value(row, "user_id")), course_id=course_id,
                course_code=value(row, "course_code"), total_questions=parse_int(row.get("total_questions")),
                correct_answers=parse_int(row.get("correct_answers")), wrong_answers=parse_int(row.get("wrong_answers")),
                unanswered=parse_int(row.get("unanswered")), score_percentage=parse_float(row.get("score_percentage")),
                time_spent_seconds=parse_int(row.get("time_spent_seconds")),
                time_allowed_seconds=parse_int(row.get("time_allowed_seconds")), passed=parse_bool(row.get("passed")),
                answers=parse_json(row.get("answers"), []),
            )
            objects.append(obj)
            audit.append((obj, *self.audit_values(row)))
        self.bulk_insert("mock_exam_results", objects, audit)

    def import_bookmarks(self):
        objects, audit = [], []
        seen_pairs = set()
        for row in self.rows["bookmarks"]:
            course_id, question_id = value(row, "course_id"), value(row, "question_id")
            if course_id not in self.course_ids or question_id not in self.question_ids:
                raise CommandError(f"Bookmark {value(row, 'id')!r} references a missing course or question.")
            user_id = self.user_id(value(row, "user_id"))
            pair = (user_id, question_id)
            if pair in seen_pairs:
                # The target schema intentionally permits one bookmark per
                # user/question. Preserve the first exported bookmark (which
                # has the same relationship) and record every duplicate that
                # is consolidated by that rule.
                self.note_import_repair("duplicate bookmark rows consolidated")
                continue
            seen_pairs.add(pair)
            obj = Bookmark(id=value(row, "id"), user_id=user_id, course_id=course_id,
                           question_id=question_id, course_code=value(row, "course_code"))
            objects.append(obj)
            audit.append((obj, *self.audit_values(row)))
        self.bulk_insert("bookmarks", objects, audit)

    def import_referrals(self):
        objects, audit = [], []
        valid_statuses = set(Referral.Status.values)
        for row in self.rows["referrals"]:
            status = value(row, "status", Referral.Status.PENDING)
            referred_id = value(row, "referred_user_id")
            obj = Referral(
                id=value(row, "id"), referrer_user_id=self.user_id(value(row, "referrer_user_id")),
                referred_user_id=self.user_id(referred_id) if referred_id else None,
                referrer_code=value(row, "referrer_code"), referred_email=value(row, "referred_email"),
                referred_name=value(row, "referred_name"), reward_amount=parse_decimal(row.get("reward_amount"), "500"),
                status=status if status in valid_statuses else Referral.Status.PENDING,
                paid_date=parse_dt(row.get("paid_date")),
            )
            objects.append(obj)
            audit.append((obj, *self.audit_values(row)))
        self.bulk_insert("referrals", objects, audit)

    def import_withdrawals(self):
        objects, audit = [], []
        valid_statuses = set(WithdrawalRequest.Status.values)
        for row in self.rows["withdrawal_requests"]:
            status = value(row, "status", WithdrawalRequest.Status.PENDING)
            obj = WithdrawalRequest(
                id=value(row, "id"), user_id=self.user_id(value(row, "user_id")),
                referral_code=value(row, "referral_code"), full_name=value(row, "full_name"),
                email=value(row, "email"), bank_name=value(row, "bank_name"),
                account_number=value(row, "account_number"), account_name=value(row, "account_name"),
                amount=parse_decimal(row.get("amount")),
                status=status if status in valid_statuses else WithdrawalRequest.Status.PENDING,
                paid_date=parse_dt(row.get("paid_date")),
            )
            objects.append(obj)
            audit.append((obj, *self.audit_values(row)))
        self.bulk_insert("withdrawal_requests", objects, audit)
