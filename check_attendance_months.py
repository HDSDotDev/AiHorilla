"""
Check attendance records by month for all employees
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from datetime import date
from collections import defaultdict
from django.apps import apps

def check_attendance_by_month():
    """Check which months have attendance records"""
    
    # Check if attendance app is installed
    if not apps.is_installed('attendance'):
        print("❌ Attendance app is not installed")
        return
    
    from attendance.models import Attendance
    from base.models import CompanyLeaves, Holidays
    from employee.models import Employee
    
    print("\n" + "="*70)
    print("ATTENDANCE RECORDS BY MONTH")
    print("="*70)
    
    # Get all attendance records
    attendances = Attendance.objects.all().order_by('attendance_date')
    
    if not attendances.exists():
        print("\n❌ NO ATTENDANCE RECORDS FOUND")
        print("\nThis explains the payroll generation failures!")
        print("The months_between_range() function may be checking for attendance")
        print("or working days, and finding none returns an empty list.")
        return
    
    print(f"\n✓ Total attendance records: {attendances.count()}")
    
    # Group by year-month
    by_month = defaultdict(lambda: {'count': 0, 'employees': set(), 'dates': set()})
    
    for att in attendances:
        month_key = f"{att.attendance_date.year}-{att.attendance_date.month:02d}"
        by_month[month_key]['count'] += 1
        by_month[month_key]['employees'].add(att.employee_id.id)
        by_month[month_key]['dates'].add(att.attendance_date)
    
    print("\n" + "-"*70)
    print("MONTHS WITH ATTENDANCE:")
    print("-"*70)
    
    for month in sorted(by_month.keys()):
        data = by_month[month]
        print(f"\n📅 {month}")
        print(f"   Records: {data['count']}")
        print(f"   Employees: {len(data['employees'])}")
        print(f"   Days covered: {len(data['dates'])}")
    
    # Check date range
    if attendances.exists():
        first = attendances.first()
        last = attendances.last()
        print(f"\n" + "="*70)
        print(f"DATE RANGE: {first.attendance_date} to {last.attendance_date}")
        print("="*70)
    
    # Check total employees
    total_active = Employee.objects.filter(is_active=True).count()
    emp_with_att = len(set(att.employee_id.id for att in attendances))
    
    print(f"\n📊 EMPLOYEE COVERAGE:")
    print(f"   Active employees: {total_active}")
    print(f"   With attendance: {emp_with_att}")
    print(f"   Missing attendance: {total_active - emp_with_att}")
    
    # Check holidays
    print(f"\n" + "="*70)
    print("HOLIDAYS & COMPANY LEAVES")
    print("="*70)
    
    holidays = Holidays.objects.all().order_by('start_date')
    print(f"\n🎉 Holidays: {holidays.count()}")
    for h in holidays[:10]:
        print(f"   - {h.start_date}: {h.name}")
    if holidays.count() > 10:
        print(f"   ... and {holidays.count() - 10} more")
    
    company_leaves = CompanyLeaves.objects.all()
    print(f"\n🏢 Company Leaves: {company_leaves.count()}")
    for cl in company_leaves:
        print(f"   - {cl}")

if __name__ == '__main__':
    check_attendance_by_month()
