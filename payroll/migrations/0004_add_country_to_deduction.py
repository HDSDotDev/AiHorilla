# Generated migration for adding country field to Deduction model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0003_payrollcountryconfig_philippinescola_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='deduction',
            name='country',
            field=models.CharField(
                choices=[('USA', 'United States'), ('PH', 'Philippines'), ('GLOBAL', 'All Countries')],
                default='GLOBAL',
                help_text='Country where this deduction applies. Select "All Countries" for universal deductions.',
                max_length=10
            ),
        ),
    ]
