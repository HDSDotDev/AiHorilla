import os
import django

os.environ['SKIP_SCHEDULERS'] = '1'
os.environ['SKIP_DB_INIT_IN_READY'] = '1'

django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name='base_company' 
    ORDER BY ordinal_position
""")

print("base_company table columns:")
print("=" * 50)
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}")
