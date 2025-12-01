# Generated migration to add Philippines payroll fields to Employee model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0001_initial'),
        ('payroll', '0005_payrollcountryconfig_constraints_and_audit'),
    ]

    operations = [
        # Add Philippines-specific payroll fields to Employee model
        migrations.AddField(
            model_name='employee',
            name='tin_number',
            field=models.CharField(
                max_length=20,
                blank=True,
                null=True,
                verbose_name='TIN (Tax Identification Number)',
                help_text='BIR Tax Identification Number (e.g., 123-456-789-000)'
            ),
        ),
        migrations.AddField(
            model_name='employee',
            name='sss_number',
            field=models.CharField(
                max_length=20,
                blank=True,
                null=True,
                verbose_name='SSS Number',
                help_text='Social Security System number (e.g., 01-2345678-9)'
            ),
        ),
        migrations.AddField(
            model_name='employee',
            name='philhealth_number',
            field=models.CharField(
                max_length=20,
                blank=True,
                null=True,
                verbose_name='PhilHealth Number',
                help_text='PhilHealth ID number (e.g., 12-345678901-2)'
            ),
        ),
        migrations.AddField(
            model_name='employee',
            name='pagibig_number',
            field=models.CharField(
                max_length=20,
                blank=True,
                null=True,
                verbose_name='Pag-IBIG Number',
                help_text='Pag-IBIG MID number (e.g., 1234-5678-9012)'
            ),
        ),
        migrations.AddField(
            model_name='employee',
            name='ph_region',
            field=models.ForeignKey(
                to='payroll.PhilippinesRegion',
                on_delete=models.SET_NULL,
                blank=True,
                null=True,
                verbose_name='Philippines Region',
                help_text='Region for minimum wage and COLA calculation',
                related_name='employees'
            ),
        ),
        migrations.AddField(
            model_name='employee',
            name='ph_tax_status',
            field=models.CharField(
                max_length=10,
                blank=True,
                null=True,
                choices=[
                    ('S', 'Single'),
                    ('ME', 'Married Employee'),
                    ('S1', 'Single with 1 dependent'),
                    ('S2', 'Single with 2 dependents'),
                    ('S3', 'Single with 3 dependents'),
                    ('S4', 'Single with 4 or more dependents'),
                    ('ME1', 'Married Employee with 1 dependent'),
                    ('ME2', 'Married Employee with 2 dependents'),
                    ('ME3', 'Married Employee with 3 dependents'),
                    ('ME4', 'Married Employee with 4 or more dependents'),
                ],
                default='S',
                verbose_name='Tax Withholding Status',
                help_text='BIR withholding tax exemption status'
            ),
        ),
        
        # Add index for faster queries
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(fields=['ph_region'], name='employee_ph_region_idx'),
        ),
    ]
