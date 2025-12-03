# Generated migration to add is_new_employee field to auth_user table
# This field is added dynamically via User.add_to_class() in base/models.py line 1865
# but requires a database column to exist

from django.db import migrations, models, connection


def add_is_new_employee_field(apps, schema_editor):
    """
    Add is_new_employee column to auth_user table.
    Compatible with both PostgreSQL and SQLite.
    """
    with connection.cursor() as cursor:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(auth_user);")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_new_employee' not in columns:
            # SQLite doesn't support ALTER TABLE ADD COLUMN with DEFAULT for NOT NULL
            # So we add as nullable first, update, then make NOT NULL
            if connection.vendor == 'sqlite':
                cursor.execute("""
                    ALTER TABLE auth_user 
                    ADD COLUMN is_new_employee BOOLEAN;
                """)
                cursor.execute("""
                    UPDATE auth_user 
                    SET is_new_employee = 0 
                    WHERE is_new_employee IS NULL;
                """)
            else:
                # PostgreSQL supports IF NOT EXISTS
                cursor.execute("""
                    ALTER TABLE auth_user 
                    ADD COLUMN IF NOT EXISTS is_new_employee BOOLEAN NOT NULL DEFAULT FALSE;
                """)


def remove_is_new_employee_field(apps, schema_editor):
    """
    Remove is_new_employee column from auth_user table.
    Compatible with both PostgreSQL and SQLite.
    """
    with connection.cursor() as cursor:
        if connection.vendor == 'sqlite':
            # SQLite doesn't support DROP COLUMN easily, skip for reverse
            pass
        else:
            cursor.execute("""
                ALTER TABLE auth_user 
                DROP COLUMN IF EXISTS is_new_employee;
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),  # Latest auth migration
    ]

    operations = [
        migrations.RunPython(
            add_is_new_employee_field,
            remove_is_new_employee_field,
        ),
    ]
