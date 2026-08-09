import os
import csv
from dateutil import parser as date_parser
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from referrals.models import WithdrawalRequest

User = get_user_model()

class Command(BaseCommand):
    help = 'Import withdrawal requests from WithdrawalRequest_export.csv'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default=r'c:\Users\partn\OneDrive\Documents\My study app\baackend data\WithdrawalRequest_export.csv')

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
                    user_id = row.get('user_id', '').strip()
                    if not user_id:
                        continue

                    user = User.objects.filter(id=user_id).first()
                    if not user:
                        continue

                    withdrawal_id = row.get('id', '').strip()
                    status_val = row.get('status', 'pending').strip()

                    withdrawal, created = WithdrawalRequest.objects.update_or_create(
                        id=withdrawal_id if withdrawal_id else None,
                        defaults={
                            'user': user,
                            'referral_code': row.get('referral_code', '').strip(),
                            'full_name': row.get('full_name', '').strip(),
                            'email': row.get('email', '').strip(),
                            'bank_name': row.get('bank_name', '').strip(),
                            'account_number': row.get('account_number', '').strip(),
                            'account_name': row.get('account_name', '').strip(),
                            'amount': float(row.get('amount', '0') or 0.0),
                            'status': status_val if status_val in dict(WithdrawalRequest.Status.choices) else WithdrawalRequest.Status.PENDING,
                            'paid_date': parse_date(row.get('paid_date', '')),
                        }
                    )
                    if created:
                        created_count += 1
                    count += 1
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Error importing withdrawal: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Withdrawal Requests import finished! Total: {count}, Created: {created_count}"))
