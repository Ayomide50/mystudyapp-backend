from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from departments.models import Department
from courses.models import Course
from questions.models import Question
from students.models import StudentProfile
from activation_codes.models import ActivationCode

User = get_user_model()

class BackendAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            email='admin@mystudyapp.com',
            password='AdminPassword123!',
            full_name='Admin User'
        )
        self.student_user = User.objects.create_user(
            email='student@mystudyapp.com',
            password='StudentPassword123!',
            full_name='Student User',
            role=User.Role.STUDENT
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            full_name='Student User',
            email=self.student_user.email,
            my_referral_code='STUDENT123'
        )

        self.department = Department.objects.create(
            name='Computer Science',
            description='CS Department',
            is_active=True,
            levels=['100', '200']
        )
        self.course = Course.objects.create(
            department=self.department,
            title='Introduction to Programming',
            code='CSC 101',
            level='100',
            is_active=True,
            question_count=1
        )
        self.question = Question.objects.create(
            course=self.course,
            question_text='What is Python?',
            option_a='A programming language',
            option_b='A snake',
            option_c='A car',
            option_d='A book',
            correct_answer='A',
            difficulty='easy',
            is_active=True
        )

    def test_user_authentication_flow(self):
        # Register user
        reg_response = self.client.post('/api/auth/register/', {
            'email': 'newstudent@mystudyapp.com',
            'password': 'NewPassword123!',
            'full_name': 'New Student'
        })
        self.assertEqual(reg_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(reg_response.data['success'])
        self.assertIn('access_token', reg_response.data)

        # Login user
        login_response = self.client.post('/api/auth/login/', {
            'email': 'newstudent@mystudyapp.com',
            'password': 'NewPassword123!'
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)
        token = login_response.data['access']

        # Get me endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        me_response = self.client.get('/api/auth/me/')
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['email'], 'newstudent@mystudyapp.com')

    def test_student_profile_me_endpoint(self):
        login_response = self.client.post('/api/auth/login/', {
            'email': self.student_user.email,
            'password': 'StudentPassword123!'
        })
        token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        profile_response = self.client.get('/api/students/me/')
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data['email'], self.student_user.email)
        self.assertEqual(profile_response.data['my_referral_code'], 'STUDENT123')

    def test_courses_and_questions_listing(self):
        login_response = self.client.post('/api/auth/login/', {
            'email': self.student_user.email,
            'password': 'StudentPassword123!'
        })
        token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # List departments
        dept_res = self.client.get('/api/departments/')
        self.assertEqual(dept_res.status_code, status.HTTP_200_OK)

        # List courses
        course_res = self.client.get(f'/api/courses/?department_id={self.department.id}')
        self.assertEqual(course_res.status_code, status.HTTP_200_OK)

        # List questions
        q_res = self.client.get(f'/api/questions/?course_id={self.course.id}')
        self.assertEqual(q_res.status_code, status.HTTP_200_OK)

    def test_admin_dashboard_stats_and_gate(self):
        login_response = self.client.post('/api/auth/login/', {
            'email': self.admin_user.email,
            'password': 'AdminPassword123!'
        })
        token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        stats_res = self.client.get('/api/admin/dashboard/stats/')
        self.assertEqual(stats_res.status_code, status.HTTP_200_OK)
        self.assertIn('total_students', stats_res.data)
        self.assertIn('total_courses', stats_res.data)

        verify_res = self.client.post('/api/admin/verify-password/', {'password': 'AdminPassword123!'})
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_res.data['authorized'])

    def test_activation_code_verify(self):
        act_code = ActivationCode.objects.create(
            code='TEST-CODE-1234',
            access_duration='full_time',
            status='unused'
        )
        login_response = self.client.post('/api/auth/login/', {
            'email': self.student_user.email,
            'password': 'StudentPassword123!'
        })
        token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        verify_res = self.client.post('/api/activation-codes/verify/', {'code': 'TEST-CODE-1234'})
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertEqual(verify_res.data['status'], 'unused')
