"""
Check detailed September 2025 attendance coverage
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from datetime import date
from attendance.models import Attendance

def check_september_details():
    """Check September 2025 attendance day by day"""
    
    print("\n" + "="*70)
    print("SEPTEMBER 2025 ATTENDANCE DETAILS")
    print("="*70)
    
    # Get September 2025 attendance
    sept_attendance = Attendance.objects.filter(
        attendance_date__year=2025,
        attendance_date__month=9
    ).order_by('attendance_date')
    
    print(f"\nTotal September records: {sept_attendance.count()}")
    
    # Group by date
    from collections import defaultdict
    by_date = defaultdict(list)
    
    for att in sept_attendance:
        by_date[att.attendance_date].append(att.employee_id.id)
    
    print(f"\nDays with attendance: {len(by_date)}")
    print("\nDay-by-day breakdown:")
    print("-" * 70)
    
    for day in range(1, 31):
        date_obj = date(2025, 9, day)
        if date_obj in by_date:
            count = len(by_date[date_obj])
            print(f"  Sep {day:2d} ({date_obj.strftime('%a')}): {count} employees")
        else:
            print(f"  Sep {day:2d} ({date_obj.strftime('%a')}): NO ATTENDANCE ❌")
    
    # Check October too
    print("\n" + "="*70)
    print("OCTOBER 2025 ATTENDANCE DETAILS")
    print("="*70)
    
    oct_attendance = Attendance.objects.filter(
        attendance_date__year=2025,
        attendance_date__month=10
    ).order_by('attendance_date')
    
    print(f"\nTotal October records: {oct_attendance.count()}")
    
    by_date_oct = defaultdict(list)
    for att in oct_attendance:
        by_date_oct[att.attendance_date].append(att.employee_id.id)
    
    print(f"Days with attendance: {len(by_date_oct)}")
    print("\nFirst 5 days:")
    for day in range(1, 6):
        date_obj = date(2025, 10, day)
        if date_obj in by_date_oct:
            count = len(by_date_oct[date_obj])
            print(f"  Oct {day:2d} ({date_obj.strftime('%a')}): {count} employees")
        else:
            print(f"  Oct {day:2d} ({date_obj.strftime('%a')}): NO ATTENDANCE")

if __name__ == '__main__':
    check_september_details()
