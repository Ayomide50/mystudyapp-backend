from django.contrib.auth import get_user_model
from students.models import StudentProfile
from referrals.models import Referral
import secrets
import string

User = get_user_model()

def generate_random_referral_code(length=10):
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def create_student_with_profile(email, password, full_name='', referral_code_entered=''):
    user = User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
        role=User.Role.STUDENT,
        status=User.Status.ACTIVE
    )
    
    my_code = generate_random_referral_code()
    profile, _ = StudentProfile.objects.get_or_create(
        user=user,
        defaults={
            'full_name': full_name or email.split('@')[0],
            'email': email,
            'my_referral_code': my_code,
            'referral_code': referral_code_entered
        }
    )

    if referral_code_entered:
        referrer_profile = StudentProfile.objects.filter(my_referral_code=referral_code_entered).first()
        if referrer_profile:
            Referral.objects.create(
                referrer_user=referrer_profile.user,
                referred_user=user,
                referrer_code=referral_code_entered,
                referred_email=email,
                referred_name=full_name or email,
                reward_amount=500.00,
                status=Referral.Status.PENDING
            )

    return user, profile
