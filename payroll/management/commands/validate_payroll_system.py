"""
Management command to validate payroll system configuration.

Run this before processing payroll to catch configuration issues early.

Usage:
    python manage.py validate_payroll_system
    python manage.py validate_payroll_system --country PH
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Validate payroll system configuration and master data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--country',
            type=str,
            choices=['PH', 'USA'],
            help='Validate specific country (PH or USA)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('PAYROLL SYSTEM VALIDATION'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write('')
        
        # Check active country configuration
        self.stdout.write('Checking active payroll country...')
        try:
            from payroll.models.country_models import PayrollCountryConfig
            
            active_country = PayrollCountryConfig.objects.filter(is_active=True).first()
            
            if not active_country:
                self.stdout.write(self.style.ERROR('✗ No active payroll country configured'))
                self.stdout.write(self.style.WARNING('  Action required: Configure active payroll country'))
                self.stdout.write(self.style.WARNING('  Run: python manage.py setup_philippines_payroll'))
                raise CommandError('No active payroll country')
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Active Country: {active_country.get_country_display()}')
            )
            
            if hasattr(active_country, 'activated_at') and active_country.activated_at:
                self.stdout.write(f'  Last activated: {active_country.activated_at}')
            
            if hasattr(active_country, 'activated_by') and active_country.activated_by:
                self.stdout.write(f'  Activated by: {active_country.activated_by}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to query active country: {e}'))
            raise CommandError('Database error accessing PayrollCountryConfig')
        
        # Check for multiple active countries (should be prevented by constraint)
        self.stdout.write('')
        self.stdout.write('Checking for configuration conflicts...')
        
        multiple_active = PayrollCountryConfig.objects.filter(is_active=True).count()
        if multiple_active > 1:
            self.stdout.write(
                self.style.ERROR(f'✗ CRITICAL: {multiple_active} countries marked as active!')
            )
            self.stdout.write(self.style.ERROR('  This will cause payroll calculation errors'))
            self.stdout.write(self.style.ERROR('  Database constraint may be missing'))
            raise CommandError('Multiple active payroll countries detected')
        
        self.stdout.write(self.style.SUCCESS('✓ No configuration conflicts found'))
        
        # Validate Philippines system if active or requested
        if active_country.country == 'PH' or options.get('country') == 'PH':
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('-' * 60))
            self.stdout.write('Validating Philippines Payroll System...')
            self.stdout.write(self.style.WARNING('-' * 60))
            
            # Check if Philippines payroll module exists
            try:
                from payroll.methods.philippines_payroll import philippines_payroll_calculation
                self.stdout.write(self.style.SUCCESS('✓ Philippines payroll module found'))
            except ImportError as e:
                self.stdout.write(self.style.ERROR('✗ Philippines payroll module NOT found'))
                self.stdout.write(self.style.ERROR(f'  Error: {e}'))
                raise CommandError('Philippines payroll module is missing')
            
            # Check validators module
            try:
                from payroll.validators import validate_ph_system_data
                self.stdout.write(self.style.SUCCESS('✓ Payroll validators module found'))
            except ImportError:
                self.stdout.write(self.style.WARNING('⚠ Payroll validators module not found'))
                self.stdout.write(self.style.WARNING('  Employee data validation will be skipped'))
                validate_ph_system_data = None
            
            # Validate PH master data
            if validate_ph_system_data:
                try:
                    validate_ph_system_data()
                    self.stdout.write(self.style.SUCCESS('✓ Philippines master data valid'))
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR('✗ Philippines system validation failed:'))
                    if hasattr(e, 'messages'):
                        for error in e.messages:
                            self.stdout.write(self.style.ERROR(f'  - {error}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'  - {str(e)}'))
                    raise CommandError('Philippines payroll system not properly configured')
            
            # Check Philippines-specific models
            self.stdout.write('')
            self.stdout.write('Checking Philippines contribution tables...')
            
            try:
                from payroll.models.country_models import (
                    PhilippinesSSSContribution,
                    PhilippinesPhilHealthContribution,
                    PhilippinesPagIbigContribution,
                    PhilippinesTaxBracket
                )
                
                # SSS
                sss_count = PhilippinesSSSContribution.objects.count()
                if sss_count > 0:
                    self.stdout.write(self.style.SUCCESS(f'✓ SSS: {sss_count} contribution tables'))
                else:
                    self.stdout.write(self.style.ERROR('✗ SSS: No contribution tables'))
                
                # PhilHealth
                philhealth_count = PhilippinesPhilHealthContribution.objects.count()
                if philhealth_count > 0:
                    self.stdout.write(self.style.SUCCESS(f'✓ PhilHealth: {philhealth_count} contribution tables'))
                else:
                    self.stdout.write(self.style.ERROR('✗ PhilHealth: No contribution tables'))
                
                # Pag-IBIG
                pagibig_count = PhilippinesPagIbigContribution.objects.count()
                if pagibig_count > 0:
                    self.stdout.write(self.style.SUCCESS(f'✓ Pag-IBIG: {pagibig_count} contribution tables'))
                else:
                    self.stdout.write(self.style.ERROR('✗ Pag-IBIG: No contribution tables'))
                
                # Tax Brackets
                tax_count = PhilippinesTaxBracket.objects.count()
                if tax_count > 0:
                    self.stdout.write(self.style.SUCCESS(f'✓ Tax Brackets: {tax_count} brackets'))
                else:
                    self.stdout.write(self.style.ERROR('✗ Tax Brackets: No brackets'))
                
                # Summary
                if sss_count == 0 or philhealth_count == 0 or pagibig_count == 0 or tax_count == 0:
                    raise CommandError('Philippines payroll master data is incomplete')
                    
            except ImportError as e:
                self.stdout.write(self.style.ERROR(f'✗ Philippines models not found: {e}'))
                raise CommandError('Philippines payroll models are not installed')
        
        # Check USA system if active
        elif active_country.country == 'USA' or options.get('country') == 'USA':
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('-' * 60))
            self.stdout.write('Validating USA Payroll System...')
            self.stdout.write(self.style.WARNING('-' * 60))
            self.stdout.write(self.style.SUCCESS('✓ USA payroll system active (default)'))
        
        # Test middleware cache
        self.stdout.write('')
        self.stdout.write('Checking middleware configuration...')
        try:
            from payroll.middleware import PayrollCountryMiddleware
            self.stdout.write(self.style.SUCCESS('✓ PayrollCountryMiddleware found'))
            
            # Check if middleware is in settings
            from django.conf import settings
            middleware_list = settings.MIDDLEWARE
            if 'payroll.middleware.PayrollCountryMiddleware' in middleware_list:
                self.stdout.write(self.style.SUCCESS('✓ Middleware is registered in settings'))
            else:
                self.stdout.write(self.style.WARNING('⚠ Middleware not found in MIDDLEWARE settings'))
                self.stdout.write(self.style.WARNING('  Add "payroll.middleware.PayrollCountryMiddleware" to MIDDLEWARE'))
        except ImportError:
            self.stdout.write(self.style.WARNING('⚠ PayrollCountryMiddleware not found'))
        
        # Final summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('PAYROLL SYSTEM VALIDATION: PASSED'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'Active Country: {active_country.get_country_display()}')
        self.stdout.write('System is ready to process payroll')
        self.stdout.write('')
