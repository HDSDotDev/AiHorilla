# Generated migration for PayrollCountryConfig constraint and audit fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0001_initial'),  # Adjust if needed
        ('payroll', '0004_add_country_to_deduction'),
    ]

    operations = [
        # Add activated_at field
        migrations.AddField(
            model_name='payrollcountryconfig',
            name='activated_at',
            field=models.DateTimeField(
                auto_now=True,
                verbose_name='Last Activated At',
                help_text='Timestamp when this country was last activated'
            ),
        ),
        
        # Add activated_by field
        migrations.AddField(
            model_name='payrollcountryconfig',
            name='activated_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payroll_country_activations',
                to='employee.employee',
                verbose_name='Activated By',
                help_text='User who last activated this country configuration'
            ),
        ),
        
        # Add unique constraint for one active country per company
        migrations.AddConstraint(
            model_name='payrollcountryconfig',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True),
                fields=('company_id',),
                name='one_active_country_per_company'
            ),
        ),
        
        # Add index for faster queries
        migrations.AddIndex(
            model_name='payrollcountryconfig',
            index=models.Index(
                fields=['is_active', 'company_id'],
                name='payroll_country_active_idx'
            ),
        ),
    ]
