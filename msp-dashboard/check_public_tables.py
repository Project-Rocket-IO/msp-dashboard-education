#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectRocket.settings.development')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    print(f'Total tables in public schema: {len(tables)}')
    
    # Look for OTP/2FA tables
    otp_tables = [t[0] for t in tables if 'otp' in t[0].lower() or 'two_factor' in t[0].lower()]
    print(f'OTP/2FA tables in public schema: {otp_tables}')
    
    # Show first 10 tables
    print('\nFirst 10 tables in public schema:')
    for i, table in enumerate(tables[:10]):
        print(f'  {i+1}. {table[0]}')
