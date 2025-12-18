"""
Quick script to assign shifts to all EmployeeWorkInformation records
"""
import os
import django
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from employee.models import EmployeeWorkInformation
from base.models import EmployeeShift, WorkType, Company

def assign_shifts():
    """Assign shifts and work types to all employees"""
    
    # Get shifts and work types
    shifts = list(EmployeeShift.objects.all())
    work_types = list(WorkType.objects.all())
    
    print(f"Found {len(shifts)} shifts")
    print(f"Found {len(work_types)} work types")
    
    # Create default shift if none exist
    if not shifts:
        print("[WARNING] No shifts found! Creating default Day Shift...")
        company = Company.objects.first()
        shift = EmployeeShift.objects.create(
            employee_shift='Day Shift',
            shift_start_time='09:00:00',
            shift_end_time='18:00:00',
            company_id=company,
        )
        shifts = [shift]
        print(f"[SUCCESS] Created default shift: {shift.employee_shift}")
    
    # Update all EmployeeWorkInformation
    work_infos = EmployeeWorkInformation.objects.all()
    print(f"\nUpdating {work_infos.count()} employee work info records...")
    
    updated_count = 0
    for work_info in work_infos:
        # Assign shift if not already assigned
        if not work_info.shift_id:
            work_info.shift_id = random.choice(shifts)
            updated_count += 1
        
        # Assign work type if not already assigned and work types exist
        if work_types and not work_info.work_type_id:
            work_info.work_type_id = random.choice(work_types)
        
        work_info.save()
    
    print(f"[SUCCESS] Updated {updated_count} employees with shifts")
    print(f"[SUCCESS] All {work_infos.count()} employees now have shifts assigned")
    
    # Verify assignments
    print("\nVerifying assignments:")
    no_shift = EmployeeWorkInformation.objects.filter(shift_id__isnull=True).count()
    has_shift = EmployeeWorkInformation.objects.filter(shift_id__isnull=False).count()
    print(f"  - Employees with shifts: {has_shift}")
    print(f"  - Employees without shifts: {no_shift}")
    
    if no_shift == 0:
        print("\n✓ ALL EMPLOYEES HAVE SHIFTS ASSIGNED!")
    else:
        print(f"\n✗ WARNING: {no_shift} employees still have no shift")

if __name__ == '__main__':
    assign_shifts()
