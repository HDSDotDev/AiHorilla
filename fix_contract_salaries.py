#!/usr/bin/env python
"""
Fix Contract Salaries - Updates all contracts with proper PHP salary ranges
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from payroll.models import Contract
from employee.models import Employee

# Philippines salary ranges by position level
SALARY_RANGES = {
    # C-Level & Senior Management (PHP 150K - 250K)
    'CEO': (200000, 250000),
    'CFO': (180000, 220000),
    'COO': (180000, 220000),
    'CTO': (180000, 220000),
    'VP': (150000, 200000),
    'Director': (120000, 180000),
    
    # Management (PHP 80K - 150K)
    'Manager': (80000, 120000),
    'Senior Manager': (100000, 150000),
    'Team Lead': (70000, 100000),
    'Project Manager': (80000, 120000),
    
    # Senior Specialists (PHP 60K - 100K)
    'Senior': (70000, 100000),
    'Lead': (80000, 110000),
    'Principal': (90000, 120000),
    'Architect': (100000, 140000),
    
    # Mid-Level (PHP 40K - 70K)
    'Developer': (40000, 70000),
    'Engineer': (45000, 75000),
    'Analyst': (40000, 70000),
    'Specialist': (45000, 70000),
    'Consultant': (50000, 80000),
    'Coordinator': (35000, 55000),
    'Officer': (38000, 60000),
    
    # Junior/Entry Level (PHP 25K - 45K)
    'Junior': (25000, 40000),
    'Associate': (28000, 45000),
    'Assistant': (25000, 38000),
    'Trainee': (22000, 30000),
    'Intern': (18000, 25000),
    
    # Support & Admin (PHP 22K - 45K)
    'Administrative': (22000, 35000),
    'Support': (25000, 40000),
    'Representative': (25000, 42000),
    'Receptionist': (20000, 28000),
}

def get_salary_for_position(position_name):
    """Determine salary based on position title keywords"""
    import random
    
    position_lower = position_name.lower()
    
    # Check each salary range keyword
    for keyword, (min_sal, max_sal) in SALARY_RANGES.items():
        if keyword.lower() in position_lower:
            # Return random salary within range
            return random.randint(min_sal, max_sal)
    
    # Default for unmatched positions (mid-level range)
    return random.randint(35000, 55000)

def fix_contract_salaries():
    """Update all contracts with appropriate salaries"""
    print("\n" + "="*80)
    print("  FIXING CONTRACT SALARIES FOR PHILIPPINES DEMO DATA")
    print("="*80 + "\n")
    
    contracts = Contract.objects.all()
    total = contracts.count()
    
    if total == 0:
        print("[ERROR] No contracts found in database!")
        return
    
    print(f"[INFO] Found {total} contracts to update\n")
    
    updated = 0
    failed = 0
    
    for contract in contracts:
        try:
            employee = contract.employee_id
            position = contract.job_position
            
            if not position:
                print(f"[WARN] Contract {contract.id} has no job position, skipping")
                failed += 1
                continue
            
            # Get appropriate salary for this position
            new_salary = get_salary_for_position(position.job_position)
            
            # Update contract
            contract.wage = float(new_salary)
            contract.contract_status = 'active'  # Ensure it's active
            contract.save()
            
            print(f"[OK] {employee.employee_first_name} {employee.employee_last_name:15} | "
                  f"{position.job_position:30} | PHP {new_salary:>9,}")
            
            updated += 1
            
        except Exception as e:
            print(f"[ERROR] Failed to update contract {contract.id}: {str(e)}")
            failed += 1
    
    print("\n" + "="*80)
    print(f"[SUCCESS] Updated {updated}/{total} contracts")
    if failed > 0:
        print(f"[WARNING] {failed} contracts failed to update")
    print("="*80 + "\n")

if __name__ == '__main__':
    try:
        fix_contract_salaries()
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
