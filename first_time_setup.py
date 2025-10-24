#!/usr/bin/env python
"""
Complete First-Time Setup for Horilla Philippines Payroll

This script handles EVERYTHING needed for a fresh installation:
1. Apply all database migrations
2. Populate Philippines payroll data
3. Configure country-specific deductions
4. Set up Philippine Peso currency
5. Activate Philippines payroll system

Usage:
    python first_time_setup.py
"""

import os
import sys
import django

# Setup Django environment
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.core.management import call_command


def print_banner():
    """Print welcome banner"""
    print("\n" + "=" * 80)
    print("  HORILLA HRMS - PHILIPPINES PAYROLL EDITION")
    print("  First-Time Setup - Complete Installation")
    print("=" * 80)
    print("\n  This script will:")
    print("  ✓ Apply all database migrations")
    print("  ✓ Create Philippines payroll tables")
    print("  ✓ Populate SSS, PhilHealth, Pag-IBIG, tax data")
    print("  ✓ Configure 17 Philippine regions")
    print("  ✓ Set up overtime rules and holidays")
    print("  ✓ Mark USA-specific deductions")
    print("  ✓ Activate Philippines payroll system")
    print("\n" + "=" * 80 + "\n")


def run_step(step_number, description, command_func):
    """Run a setup step and handle errors"""
    print(f"\n[{step_number}/6] {description}")
    print("-" * 80)
    
    try:
        command_func()
        print(f"✅ Step {step_number} completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Step {step_number} failed: {e}")
        print(f"   You may need to run this step manually")
        return False


def step1_migrations():
    """Apply all database migrations"""
    print("   Running: python manage.py migrate")
    call_command('migrate', verbosity=1, interactive=False)


def step2_populate_data():
    """Populate Philippines payroll data"""
    print("   Populating Philippines data...")
    call_command('populate_ph_payroll')


def step3_update_deductions():
    """Update deduction countries"""
    print("   Updating deduction countries...")
    call_command('update_deduction_countries')


def step4_activate_philippines():
    """Activate Philippines payroll"""
    from payroll.models.country_models import PayrollCountryConfig
    
    print("   Activating Philippines payroll system...")
    ph_config, created = PayrollCountryConfig.objects.get_or_create(
        country='PH',
        defaults={'is_active': True}
    )
    
    if not ph_config.is_active:
        PayrollCountryConfig.objects.exclude(country='PH').update(is_active=False)
        ph_config.is_active = True
        ph_config.save()
        print("   ✓ Philippines activated (USA deactivated)")
    else:
        print("   ✓ Philippines already active")


def step5_setup_currency():
    """Set Philippine Peso currency"""
    from payroll.models.tax_models import PayrollSettings
    
    print("   Setting currency to Philippine Peso (₱)...")
    settings, created = PayrollSettings.objects.get_or_create(
        company_id=None,
        defaults={
            'currency_symbol': '₱',
            'position': 'prefix'
        }
    )
    
    if not created:
        settings.currency_symbol = '₱'
        settings.position = 'prefix'
        settings.save()
    
    print("   ✓ Currency set to ₱ (Philippine Peso)")


def step6_verify_setup():
    """Verify setup completed correctly"""
    from payroll.models.country_models import (
        PhilippinesSSSContribution,
        PhilippinesTaxBracket,
        PhilippinesRegion,
        PhilippinesOvertimeRule,
        PhilippinesHolidayPay,
        PayrollCountryConfig
    )
    from payroll.models.models import Deduction
    
    print("   Verifying installation...")
    
    checks = [
        ("SSS Brackets", PhilippinesSSSContribution.objects.count(), 52),
        ("Tax Brackets", PhilippinesTaxBracket.objects.count(), 6),
        ("Regions", PhilippinesRegion.objects.count(), 17),
        ("Overtime Rules", PhilippinesOvertimeRule.objects.count(), 7),
        ("Holidays (2025)", PhilippinesHolidayPay.objects.count(), 16),
        ("USA Deductions", Deduction.objects.filter(country='USA').count(), 3),
    ]
    
    all_passed = True
    for name, actual, expected in checks:
        status = "✓" if actual >= expected else "✗"
        print(f"   {status} {name}: {actual} (expected {expected})")
        if actual < expected:
            all_passed = False
    
    # Check if Philippines is active
    ph_active = PayrollCountryConfig.objects.filter(country='PH', is_active=True).exists()
    status = "✓" if ph_active else "✗"
    print(f"   {status} Philippines Active: {ph_active}")
    if not ph_active:
        all_passed = False
    
    return all_passed


def print_success():
    """Print success message and next steps"""
    print("\n" + "=" * 80)
    print("  🎉 SETUP COMPLETE! Philippines Payroll System is Ready!")
    print("=" * 80)
    print("\n📋 NEXT STEPS:\n")
    
    print("1. Create Admin Account (if you haven't already):")
    print("   python manage.py createsuperuser")
    print()
    
    print("2. Start the Development Server:")
    print("   python manage.py runserver")
    print()
    
    print("3. Access the Application:")
    print("   URL: http://127.0.0.1:8000/")
    print("   Admin: http://127.0.0.1:8000/admin/")
    print()
    
    print("4. Verify Philippines is Active:")
    print("   Django Admin → Payroll → Payroll Country Configs")
    print("   ✓ Philippines (PH) should be marked as 'Is Active'")
    print()
    
    print("5. Create Your First Employee:")
    print("   - Add employee basic info")
    print("   - Create employee contract with salary")
    print("   - Add government IDs (SSS, PhilHealth, Pag-IBIG, TIN)")
    print("   - Select region (NCR, Region I, etc.)")
    print()
    
    print("6. Generate Your First Payslip:")
    print("   Payroll → Generate Payslip")
    print("   ✓ SSS, PhilHealth, Pag-IBIG auto-calculated")
    print("   ✓ BIR Withholding Tax computed")
    print("   ✓ No USA deductions (PF, PT, ESI) will appear!")
    print()
    
    print("📖 Documentation:")
    print("   - Setup Guide: SETUP_README.md")
    print("   - Philippines Guide: PHILIPPINES_PAYROLL_GUIDE.md")
    print("   - Country Deductions: COUNTRY_DEDUCTIONS_GUIDE.md")
    print("   - Solution Summary: SOLUTION_SUMMARY.md")
    print()
    
    print("=" * 80)
    print("  Ready to process Philippine payroll! 🇵🇭")
    print("=" * 80 + "\n")


def print_failure():
    """Print failure message"""
    print("\n" + "=" * 80)
    print("  ⚠️  SETUP INCOMPLETE - Some Steps Failed")
    print("=" * 80)
    print("\nPlease review the errors above and:")
    print("1. Fix any issues mentioned")
    print("2. Run the failed steps manually")
    print("3. Or run this script again: python first_time_setup.py")
    print()
    print("For help, see: SETUP_README.md")
    print("=" * 80 + "\n")


def main():
    """Main setup orchestration"""
    print_banner()
    
    # Track overall success
    all_success = True
    
    # Step 1: Migrations
    if not run_step(1, "Applying Database Migrations", step1_migrations):
        print("\n❌ CRITICAL: Migrations failed. Cannot continue.")
        print("   Try running manually: python manage.py migrate")
        return
    
    # Step 2: Populate Data
    if not run_step(2, "Populating Philippines Payroll Data", step2_populate_data):
        all_success = False
    
    # Step 3: Update Deductions
    if not run_step(3, "Updating Deduction Countries", step3_update_deductions):
        all_success = False
    
    # Step 4: Activate Philippines
    if not run_step(4, "Activating Philippines Payroll System", step4_activate_philippines):
        all_success = False
    
    # Step 5: Setup Currency
    if not run_step(5, "Setting Up Philippine Peso Currency", step5_setup_currency):
        all_success = False
    
    # Step 6: Verify
    print("\n[6/6] Verifying Setup")
    print("-" * 80)
    verification_passed = step6_verify_setup()
    
    if verification_passed:
        print("✅ Step 6 completed successfully!")
    else:
        print("⚠️  Step 6: Some checks failed")
        all_success = False
    
    # Final output
    if all_success and verification_passed:
        print_success()
    else:
        print_failure()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user.")
        print("   Run the script again to complete setup: python first_time_setup.py\n")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        print("   Please report this issue with the error details above.\n")
        import traceback
        traceback.print_exc()
