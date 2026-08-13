import os
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_3DkCO8SwzFWg@ep-late-dream-aw7qtb67-pooler.c-12.us-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require'
os.environ['DJANGO_SETTINGS_MODULE'] = 'MyStudyApp.settings'
import django
from django.core.management import call_command
from django.db import connection

django.setup()
print('DJANGO DB CONFIG:', connection.settings_dict)
connection.ensure_connection()
print('CONNECTED SUCCESS')
