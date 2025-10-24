"""
Initialize Philippines Payroll System

This script helps you set up the Philippines payroll system.
Run this after migrations to get started quickly.
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.core.management import call_command
from payroll.models.country_models import PayrollCountryConfig
from payroll.models.tax_models import PayrollSettings


def print_banner():
    """Print welcome banner"""
    print("=" * 70)
    print("  PHILIPPINES PAYROLL SYSTEM SETUP")
    print("  Horilla HRMS - Complete PH Compliance")
    print("=" * 70)
    print()


def check_migrations():
    """Check if migrations are applied"""
    print("📋 Checking migrations...")
    try:
        # Try to query a model to check if migrations are applied
        PayrollCountryConfig.objects.first()
        print("✅ Migrations are applied")
        return True
    except Exception as e:
        print("❌ Migrations not applied. Please run:")
        print("   python manage.py makemigrations payroll")
        print("   python manage.py migrate")
        return False


def populate_data():
    """Populate Philippines payroll data"""
    print("\n📊 Populating Philippines payroll data...")
    print("   This includes:")
    print("   - SSS contribution tables (51 brackets)")
    print("   - PhilHealth contribution rates")
    print("   - Pag-IBIG contribution rates")
    print("   - BIR tax brackets (TRAIN Law)")
    print("   - 17 Philippines regions with minimum wage")
    print("   - Overtime rules (7 types)")
    print("   - 2025 holidays (16 holidays)")
    print("   - 13th month pay configuration")
    print()
    
    try:
        call_command('populate_ph_payroll')
        print("✅ Data populated successfully!")
        return True
    except Exception as e:
        print(f"❌ Error populating data: {e}")
        return False


def activate_philippines():
    """Activate Philippines as the payroll country"""
    print("\n🌏 Activating Philippines payroll system...")
    
    try:
        # Create Philippines config if it doesn't exist
        ph_config, created = PayrollCountryConfig.objects.get_or_create(
            country='PH',
            defaults={'is_active': True}
        )
        
        if not created and not ph_config.is_active:
            # Deactivate all other countries
            PayrollCountryConfig.objects.exclude(country='PH').update(is_active=False)
            # Activate Philippines
            ph_config.is_active = True
            ph_config.save()
            print("✅ Philippines payroll system activated!")
        elif created:
            print("✅ Philippines payroll system created and activated!")
        else:
            print("ℹ️  Philippines payroll system is already active")
        
        return True
    except Exception as e:
        print(f"❌ Error activating Philippines: {e}")
        return False


def setup_currency():
    """Set Philippine Peso as currency"""
    print("\n💱 Setting up currency...")
    
    try:
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
            print("✅ Currency updated to Philippine Peso (₱)")
        else:
            print("✅ Currency set to Philippine Peso (₱)")
        
        return True
    except Exception as e:
        print(f"❌ Error setting currency: {e}")
        return False


def update_deduction_countries():
    """Update existing deductions with country information"""
    print("\n🌍 Updating deduction countries...")
    print("   Marking USA-specific deductions (PF, PT, ESI)...")
    
    try:
        call_command('update_deduction_countries')
        print("✅ Deduction countries updated!")
        return True
    except Exception as e:
        print(f"❌ Error updating deduction countries: {e}")
        print("   You can run this manually later:")
        print("   python manage.py update_deduction_countries")
        return False


def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "=" * 70)
    print("  SETUP COMPLETE! 🎉")
    print("=" * 70)
    print("\nNext Steps:")
    print()
    print("1. Access Django Admin:")
    print("   URL: http://localhost:8000/admin/")
    print("   Go to: Payroll → Payroll Country Configurations")
    print("   Verify: Philippines is marked as 'Active'")
    print()
    print("2. Configure Employees:")
    print("   Add employee government IDs:")
    print("   - SSS Number (format: 01-2345678-9)")
    print("   - PhilHealth Number (format: 12-345678901-2)")
    print("   - Pag-IBIG Number (format: 1234-5678-9012)")
    print("   - TIN Number (format: 123-456-789-000)")
    print("   - Select employee region (NCR, Region I, etc.)")
    print()
    print("3. Start Generating Payslips:")
    print("   Navigate to: Payroll → Generate Payslip")
    print("   All Philippines fields are available:")
    print("   ✓ SSS, PhilHealth, Pag-IBIG (auto-calculated)")
    print("   ✓ Withholding Tax (BIR TRAIN Law)")
    print("   ✓ Overtime pay (125%, 130%, etc.)")
    print("   ✓ Night differential (10%)")
    print("   ✓ 13th month pay")
    print("   ✓ COLA, allowances")
    print()
    print("4. Government Reports:")
    print("   Generate required reports:")
    print("   - BIR Form 2316 (Annual ITR)")
    print("   - Alphalist")
    print("   - SSS R3/R5 Forms")
    print("   - PhilHealth RF-1")
    print("   - Pag-IBIG MCRF")
    print()
    print("📖 For detailed guide, see: PHILIPPINES_PAYROLL_GUIDE.md")
    print("=" * 70)


def main():
    """Main setup function"""
    print_banner()
    
    # Check migrations
    if not check_migrations():
        return
    
    # Populate data
    if not populate_data():
        print("\n⚠️  Setup incomplete. Please fix the errors and try again.")
        return
    
    # Activate Philippines
    if not activate_philippines():
        print("\n⚠️  Setup incomplete. Please fix the errors and try again.")
        return
    
    # Setup currency
    if not setup_currency():
        print("\n⚠️  Currency setup failed, but you can set it manually in Django Admin.")
    
    # Update deduction countries
    if not update_deduction_countries():
        print("\n⚠️  Deduction countries not updated. You can do this manually later.")
    
    # Print next steps
    print_next_steps()


if __name__ == '__main__':
    main()
