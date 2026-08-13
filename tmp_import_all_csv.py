import os
import django
from django.core.management import call_command

os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_3DkCO8SwzFWg@ep-late-dream-aw7qtb67-pooler.c-12.us-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require'
os.environ['DJANGO_SETTINGS_MODULE'] = 'MyStudyApp.settings'

print('STARTING DJANGO SETUP')
django.setup()
print('DJANGO SETUP COMPLETE')
from django.db import connection
print('DB SETTINGS:', connection.settings_dict)
connection.ensure_connection()
print('DB CONNECTED')

print('RUNNING MIGRATE')
call_command('migrate', interactive=False)
print('MIGRATE COMPLETE')

print('RUNNING IMPORT')
call_command('import_all_csv', data_dir='..\\baackend data')
print('IMPORT COMPLETE')
