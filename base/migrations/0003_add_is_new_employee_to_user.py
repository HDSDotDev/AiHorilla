# Generated migration to add is_new_employee field to auth_user table
# This field is added dynamically via User.add_to_class() in base/models.py line 1865
# but requires a database column to exist

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),  # Latest auth migration
    ]

    operations = [
        migrations.RunSQL(
            # Add the column directly to auth_user table
            sql="""
                ALTER TABLE auth_user 
                ADD COLUMN IF NOT EXISTS is_new_employee BOOLEAN NOT NULL DEFAULT FALSE;
            """,
            reverse_sql="""
                ALTER TABLE auth_user 
                DROP COLUMN IF EXISTS is_new_employee;
            """,
        ),
    ]
