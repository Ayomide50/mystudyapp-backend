import os
import csv
from dateutil import parser as date_parser
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from referrals.models import Referral

User = get_user_model()

class Command(BaseCommand):
    help = 'Import referrals from Referral_export.csv'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default=r'c:\Users\partn\OneDrive\Documents\My study app\baackend data\Referral_export.csv')

    def handle(self, *args, **options):
        file_path = options['path']
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Starting import from {file_path}..."))
        count = 0
        created_count = 0

        def parse_date(date_str):
            if not date_str: return None
            try:
                return date_parser.parse(date_str)
            except:
                return None

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    referrer_id = row.get('referrer_user_id', '').strip()
                    referred_id = row.get('referred_user_id', '').strip()

                    if not referrer_id:
                        continue

                    referrer = User.objects.filter(id=referrer_id).first()
                    if not referrer:
                        continue

                    referred = User.objects.filter(id=referred_id).first() if referred_id else None
                    
                    referral_id = row.get('id', '').strip()
                    status_val = row.get('status', 'pending').strip()

                    referral, created = Referral.objects.update_or_create(
                        id=referral_id if referral_id else None,
                        defaults={
                            'referrer_user': referrer,
                            'referred_user': referred,
                            'referrer_code': row.get('referrer_code', '').strip(),
                            'referred_email': row.get('referred_email', '').strip(),
                            'referred_name': row.get('referred_name', '').strip(),
                            'reward_amount': float(row.get('reward_amount', '500') or 500.0),
                            'status': status_val if status_val in dict(Referral.Status.choices) else Referral.Status.PENDING,
                            'paid_date': parse_date(row.get('paid_date', '')),
                        }
                    )
                    if created:
                        created_count += 1
                    count += 1
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Error importing referral: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Referrals import finished! Total: {count}, Created: {created_count}"))
