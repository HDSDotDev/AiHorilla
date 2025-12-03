# Generated migration for adding country field to Deduction model
# NOTE: The country field already exists in migration 0001_initial.py (line 101)
# This migration is kept for dependency chain but has no operations

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0003_payrollcountryconfig_philippinescola_and_more'),
    ]

    operations = [
        # No operations - country field already exists in Deduction model from migration 0001
    ]
