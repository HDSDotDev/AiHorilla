#!/usr/bin/env python
"""
COMPREHENSIVE PHILIPPINES DEMO DATA LOADER

This script populates the Railway PostgreSQL database with complete Philippine demo data:
- Company structure (BizBloqs BV - Philippines)
- 30-50 employees with varying salaries
- Complete attendance data for September & October 2025
- Leave requests, approvals, and balances
- Asset allocations
- Helpdesk tickets
- Sample payslips and payroll data
- Government IDs and compliance data

This replaces the "Load Demo Data" button functionality with PH-specific content.
"""

import os
import sys
import django
from datetime import datetime, date, timedelta, time
from decimal import Decimal
import random

# Setup Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from django.apps import apps

# Core models
from employee.models import Employee, EmployeeWorkInformation, EmployeeBankDetails
from base.models import (
    Company, Department, JobPosition, WorkType, 
    EmployeeShift, EmployeeType, ShiftRequest
)

# Payroll models
from payroll.models.models import Contract, Payslip, Allowance, Deduction
from payroll.models.country_models import (
    PhilippinesRegion, 
    PhilippinesCOLA,
    PayrollCountryConfig
)

# Attendance models (if installed)
if apps.is_installed('attendance'):
    from attendance.models import (
        Attendance, AttendanceActivity, 
        AttendanceOverTime, AttendanceValidationCondition
    )

# Leave models (if installed)
if apps.is_installed('leave'):
    from leave.models import (
        LeaveType, LeaveRequest, 
        AvailableLeave, LeaveAllocationRequest,
        CompanyLeave, Holiday
    )

# Asset models (if installed)
if apps.is_installed('asset'):
    from asset.models import (
        AssetCategory, Asset, AssetAssignment,
        AssetRequest, AssetLot
    )

# Helpdesk models (if installed)
if apps.is_installed('helpdesk'):
    from helpdesk.models import Ticket, TicketType, FAQ

# Philippine Configuration
COMPANY_NAME = "BizBloqs BV Philippines"
COMPANY_TIN = "123-456-789-000"
COMPANY_ADDRESS = "8th Floor, Net One Center, 26th St corner 3rd Ave, Bonifacio Global City, Taguig, 1634 Metro Manila"

# Philippine regions
REGIONS = {
    'NCR': ('National Capital Region', 570.00),
    'CAR': ('Cordillera Administrative Region', 470.00),
    'Region III': ('Central Luzon', 500.00),
    'Region IV-A': ('CALABARZON', 470.00),
}

# Tax statuses
TAX_STATUSES = ['S', 'S1', 'S2', 'S3', 'S4', 'ME', 'ME1', 'ME2', 'ME3', 'ME4']

# Job positions with salary ranges (monthly PHP)
POSITIONS_SALARIES = {
    'Chief Technology Officer': (150000, 250000),
    'Engineering Manager': (100000, 180000),
    'Senior Software Engineer': (70000, 120000),
    'Software Engineer': (45000, 80000),
    'Junior Software Engineer': (30000, 50000),
    'Product Manager': (80000, 140000),
    'Project Manager': (60000, 100000),
    'Business Analyst': (45000, 75000),
    'QA Engineer': (35000, 60000),
    'Senior QA Engineer': (50000, 85000),
    'DevOps Engineer': (55000, 95000),
    'UX/UI Designer': (40000, 70000),
    'Senior UX/UI Designer': (60000, 95000),
    'Data Analyst': (45000, 75000),
    'HR Manager': (60000, 95000),
    'HR Specialist': (35000, 55000),
    'Accountant': (40000, 65000),
    'Finance Manager': (70000, 110000),
    'Administrative Assistant': (25000, 38000),
    'Sales Manager': (70000, 120000),
    'Sales Executive': (30000, 50000),
    'Customer Support Specialist': (28000, 42000),
    'IT Support Specialist': (32000, 50000),
}

# Filipino names pool (100+ names)
FIRST_NAMES_MALE = [
    'Juan', 'Jose', 'Pedro', 'Miguel', 'Antonio', 'Manuel', 'Francisco', 'Carlos',
    'Ramon', 'Luis', 'Ricardo', 'Gabriel', 'Rafael', 'Fernando', 'Eduardo',
    'Daniel', 'Roberto', 'Angelo', 'Mark', 'Christian', 'John', 'Paul', 'Ryan',
    'Joshua', 'David', 'James', 'Michael', 'Joseph', 'Nathan', 'Joshua',
]

FIRST_NAMES_FEMALE = [
    'Maria', 'Ana', 'Rosa', 'Carmen', 'Luz', 'Elena', 'Sofia', 'Isabel',
    'Teresa', 'Angelica', 'Patricia', 'Michelle', 'Christine', 'Jennifer',
    'Angela', 'Kristine', 'Melissa', 'Anna', 'Sophia', 'Isabella', 'Emma',
    'Grace', 'Faith', 'Hope', 'Joy', 'Angel', 'Mae', 'Jane', 'Nicole', 'Andrea',
]

LAST_NAMES = [
    'Santos', 'Reyes', 'Cruz', 'Bautista', 'Garcia', 'Mendoza', 'Torres',
    'Lopez', 'Gonzales', 'Flores', 'Rivera', 'Ramos', 'Gomez', 'Fernandez',
    'Sanchez', 'Ramirez', 'Castro', 'Aquino', 'Diaz', 'Morales', 'Hernandez',
    'Perez', 'Domingo', 'Villanueva', 'Mercado', 'Santiago', 'Navarro',
    'Del Rosario', 'Tan', 'Lim', 'Sy', 'Ong', 'Lee', 'Chan', 'Go',
]

# Philippine holidays 2025
PH_HOLIDAYS_2025 = [
    ('2025-01-01', 'New Year\'s Day'),
    ('2025-02-25', 'EDSA People Power Revolution'),
    ('2025-04-09', 'Araw ng Kagitingan'),
    ('2025-04-17', 'Maundy Thursday'),
    ('2025-04-18', 'Good Friday'),
    ('2025-05-01', 'Labor Day'),
    ('2025-06-12', 'Independence Day'),
    ('2025-08-21', 'Ninoy Aquino Day'),
    ('2025-08-25', 'National Heroes Day'),
    ('2025-11-01', 'All Saints\' Day'),
    ('2025-11-30', 'Bonifacio Day'),
    ('2025-12-25', 'Christmas Day'),
    ('2025-12-30', 'Rizal Day'),
]


class PhilippinesComprehensiveDemo:
    """Complete Philippines demo data generator"""
    
    def __init__(self, num_employees=40):
        self.num_employees = num_employees
        self.company = None
        self.departments = []
        self.positions = {}
        self.work_types = []
        self.employee_types = []
        self.shifts = {}
        self.regions = {}
        self.employees = []
        self.leave_types = {}
        self.asset_categories = {}
        self.ticket_types = {}
        
    def log(self, message, level='info'):
        """Print formatted log message"""
        symbols = {'info': '✓', 'warn': '⚠', 'error': '✗', 'step': '▸'}
        symbol = symbols.get(level, '•')
        print(f"   {symbol} {message}")
    
    def header(self, title):
        """Print section header"""
        print(f"\n[{title.upper()}]")
    
    def create_company_and_structure(self):
        """Create company, departments, and positions"""
        self.header("Company Structure")
        
        with transaction.atomic():
            # Company
            self.company, _ = Company.objects.get_or_create(
                company=COMPANY_NAME,
                defaults={
                    'address': COMPANY_ADDRESS,
                    'country': 'Philippines',
                    'state': 'Metro Manila',
                    'city': 'Taguig',
                    'zip': '1634',
                    'icon': '',
                }
            )
            self.log(f"Company: {self.company.company}")
            
            # Departments
            dept_names = [
                'Engineering', 'Product', 'Design', 'Quality Assurance',
                'Operations', 'Sales', 'Marketing', 'Human Resources',
                'Finance', 'Customer Support', 'IT'
            ]
            
            for dept_name in dept_names:
                dept, _ = Department.objects.get_or_create(
                    department=dept_name,
                    defaults={'company_id': self.company}
                )
                self.departments.append(dept)
            
            self.log(f"Created {len(self.departments)} departments")
            
            # Create positions
            for position_name, salary_range in POSITIONS_SALARIES.items():
                # Assign department based on position name
                if 'Engineer' in position_name or 'DevOps' in position_name or 'Technology' in position_name:
                    dept = next((d for d in self.departments if d.department == 'Engineering'), self.departments[0])
                elif 'Designer' in position_name or 'UX' in position_name:
                    dept = next((d for d in self.departments if d.department == 'Design'), self.departments[0])
                elif 'QA' in position_name or 'Quality' in position_name:
                    dept = next((d for d in self.departments if d.department == 'Quality Assurance'), self.departments[0])
                elif 'HR' in position_name:
                    dept = next((d for d in self.departments if d.department == 'Human Resources'), self.departments[0])
                elif 'Account' in position_name or 'Finance' in position_name:
                    dept = next((d for d in self.departments if d.department == 'Finance'), self.departments[0])
                elif 'Sales' in position_name:
                    dept = next((d for d in self.departments if d.department == 'Sales'), self.departments[0])
                elif 'Product' in position_name or 'Project' in position_name or 'Business' in position_name:
                    dept = next((d for d in self.departments if d.department == 'Product'), self.departments[0])
                elif 'Support' in position_name or 'IT' in position_name:
                    dept = next((d for d in self.departments if d.department == 'IT'), self.departments[0])
                else:
                    dept = next((d for d in self.departments if d.department == 'Operations'), self.departments[0])
                
                position, _ = JobPosition.objects.get_or_create(
                    job_position=position_name,
                    defaults={'department_id': dept}
                )
                self.positions[position_name] = position
            
            self.log(f"Created {len(self.positions)} job positions")
            
            # Work types
            work_type, _ = WorkType.objects.get_or_create(
                work_type='Full-time',
                defaults={'company_id': self.company}
            )
            self.work_types.append(work_type)
            
            # Employee types
            emp_type, _ = EmployeeType.objects.get_or_create(
                employee_type='Permanent',
                defaults={'company_id': self.company}
            )
            self.employee_types.append(emp_type)
            
            # Shifts
            day_shift, _ = EmployeeShift.objects.get_or_create(
                employee_shift='Day Shift (9AM-6PM)',
                defaults={}
            )
            self.shifts['day'] = day_shift
            
            self.log("Created work types, employee types, and shifts")
    
    def create_philippines_regions(self):
        """Create PH regions"""
        self.header("Philippines Regions")
        
        for code, (name, wage) in REGIONS.items():
            region, _ = PhilippinesRegion.objects.get_or_create(
                region_code=code,
                defaults={
                    'region_name': name,
                    'minimum_wage': Decimal(str(wage))
                }
            )
            self.regions[code] = region
        
        self.log(f"Created {len(self.regions)} regions")
    
    def generate_government_ids(self):
        """Generate realistic PH IDs"""
        return {
            'tin': f"{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(0,999):03d}",
            'sss': f"{random.randint(10,99)}-{random.randint(1000000,9999999)}-{random.randint(0,9)}",
            'philhealth': f"{random.randint(10,99)}-{random.randint(100000000,999999999)}-{random.randint(0,9)}",
            'pagibig': f"{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
        }
    
    def create_employees(self):
        """Create employees with varying salaries"""
        self.header(f"Creating {self.num_employees} Employees")
        
        position_names = list(POSITIONS_SALARIES.keys())
        region_codes = list(self.regions.keys())
        
        for i in range(self.num_employees):
            # Generate name
            gender = random.choice(['male', 'female'])
            first_name = random.choice(FIRST_NAMES_MALE if gender == 'male' else FIRST_NAMES_FEMALE)
            last_name = random.choice(LAST_NAMES)
            username = f"{first_name.lower()}.{last_name.lower().replace(' ', '')}{random.randint(10,99)}"
            email = f"{username}@bizbloqs.ph"
            
            # Select position and salary
            position_name = random.choice(position_names)
            position = self.positions[position_name]
            salary_min, salary_max = POSITIONS_SALARIES[position_name]
            monthly_salary = random.randint(salary_min, salary_max)
            monthly_salary = round(monthly_salary / 1000) * 1000  # Round to nearest 1000
            
            # Government IDs
            gov_ids = self.generate_government_ids()
            
            # Region and tax status
            region_code = random.choice(region_codes)
            region = self.regions[region_code]
            tax_status = random.choice(TAX_STATUSES)
            
            # Hire date (employed between 6 months to 3 years ago)
            days_ago = random.randint(180, 1095)
            hire_date = date.today() - timedelta(days=days_ago)
            
            # Birth date (25-45 years old)
            age = random.randint(25, 45)
            birth_year = date.today().year - age
            dob = date(birth_year, random.randint(1, 12), random.randint(1, 28))
            
            with transaction.atomic():
                # Create user
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_active': True,
                    }
                )
                if created:
                    user.set_password('Demo@2025')
                    user.save()
                
                # Create employee
                employee, created = Employee.objects.get_or_create(
                    employee_user_id=user,
                    defaults={
                        'employee_first_name': first_name,
                        'employee_last_name': last_name,
                        'email': email,
                        'phone': f"+63{random.randint(900,999)}{random.randint(1000000,9999999)}",
                        'badge_id': f"BZQ-{i+1:04d}",
                        'gender': gender,
                        'dob': dob,
                        'address': f"Unit {random.randint(1,50)}, Bldg {random.randint(1,20)}, {random.choice(['Makati', 'Taguig', 'Pasig', 'Quezon City', 'Mandaluyong'])}, Metro Manila",
                        'country': 'Philippines',
                        'state': 'Metro Manila',
                        'city': random.choice(['Makati', 'Taguig', 'Pasig', 'Quezon City', 'Manila', 'Mandaluyong']),
                        'zip': random.choice(['1200', '1630', '1600', '1100', '1550']),
                        'is_active': True,
                        'tin_number': gov_ids['tin'],
                        'sss_number': gov_ids['sss'],
                        'philhealth_number': gov_ids['philhealth'],
                        'pagibig_number': gov_ids['pagibig'],
                        'ph_region': region,
                        'ph_tax_status': tax_status,
                    }
                )
                
                if not created:
                    continue
                
                # Work information
                work_info, _ = EmployeeWorkInformation.objects.get_or_create(
                    employee_id=employee,
                    defaults={
                        'company_id': self.company,
                        'job_position_id': position,
                        'department_id': position.department_id,
                        'work_type_id': self.work_types[0] if self.work_types else None,
                        'employee_type_id': self.employee_types[0] if self.employee_types else None,
                        'shift_id': self.shifts.get('day'),
                        'email': email,
                        'mobile': employee.phone,
                        'date_joining': hire_date,
                        'contract_start_date': hire_date,
                        'contract_end_date': hire_date + timedelta(days=730),  # 2 years
                    }
                )
                
                # Contract
                contract, _ = Contract.objects.get_or_create(
                    employee_id=employee,
                    defaults={
                        'contract_name': f"{first_name} {last_name} - Employment Contract",
                        'contract_start_date': hire_date,
                        'contract_end_date': hire_date + timedelta(days=730),
                        'wage': Decimal(str(monthly_salary)),
                        'wage_type': 'monthly',
                    }
                )
                
                # Bank details
                EmployeeBankDetails.objects.get_or_create(
                    employee_id=employee,
                    defaults={
                        'bank_name': random.choice(['BDO', 'BPI', 'Metrobank', 'UnionBank', 'Security Bank', 'Landbank']),
                        'account_number': f"{random.randint(1000,9999)}{random.randint(10000000,99999999)}",
                        'any_other_code1': f"SWIFT{random.randint(1000,9999)}",
                    }
                )
                
                self.employees.append(employee)
            
            if (i + 1) % 10 == 0:
                self.log(f"Created {i+1}/{self.num_employees} employees...")
        
        self.log(f"Successfully created {len(self.employees)} employees with salaries ranging from ₱25k to ₱250k")
    
    def create_attendance_data(self):
        """Create attendance for September and October 2025"""
        if not apps.is_installed('attendance'):
            self.log("Attendance module not installed - skipping", 'warn')
            return
        
        self.header("Attendance Data (Sep & Oct 2025)")
        
        # Date ranges
        sept_start = date(2025, 9, 1)
        sept_end = date(2025, 9, 30)
        oct_start = date(2025, 10, 1)
        oct_end = date(2025, 10, 31)
        
        attendance_count = 0
        
        for employee in self.employees:
            # Get employee's work schedule
            shift = self.shifts.get('day')
            
            # Generate attendance for September
            current_date = sept_start
            while current_date <= sept_end:
                # Skip weekends (Saturday=5, Sunday=6)
                if current_date.weekday() < 5:
                    # 95% attendance rate (5% absences)
                    if random.random() < 0.95:
                        # Clock in time (8:00 AM - 9:30 AM)
                        check_in_hour = random.randint(8, 9)
                        check_in_minute = random.randint(0, 59) if check_in_hour == 8 else random.randint(0, 30)
                        check_in = datetime.combine(current_date, time(check_in_hour, check_in_minute))
                        
                        # Work duration (8-10 hours)
                        work_hours = random.randint(8, 10)
                        check_out = check_in + timedelta(hours=work_hours, minutes=random.randint(0, 59))
                        
                        # Calculate hours
                        worked_hours = (check_out - check_in).total_seconds() / 3600
                        at_work = min(worked_hours, 8.0)  # Standard 8 hours
                        overtime = max(0, worked_hours - 8.0)
                        
                        Attendance.objects.get_or_create(
                            employee_id=employee,
                            attendance_date=current_date,
                            defaults={
                                'attendance_clock_in': check_in,
                                'attendance_clock_out': check_out,
                                'attendance_worked_hour': f"{int(worked_hours):02d}:{int((worked_hours % 1) * 60):02d}",
                                'at_work': at_work,
                                'overtime_second': int(overtime * 3600),
                                'attendance_validated': True,
                                'is_validate_request': False,
                                'is_validate_request_approved': False,
                            }
                        )
                        attendance_count += 1
                
                current_date += timedelta(days=1)
            
            # Generate attendance for October
            current_date = oct_start
            while current_date <= oct_end:
                if current_date.weekday() < 5:
                    if random.random() < 0.95:
                        check_in_hour = random.randint(8, 9)
                        check_in_minute = random.randint(0, 59) if check_in_hour == 8 else random.randint(0, 30)
                        check_in = datetime.combine(current_date, time(check_in_hour, check_in_minute))
                        
                        work_hours = random.randint(8, 10)
                        check_out = check_in + timedelta(hours=work_hours, minutes=random.randint(0, 59))
                        
                        worked_hours = (check_out - check_in).total_seconds() / 3600
                        at_work = min(worked_hours, 8.0)
                        overtime = max(0, worked_hours - 8.0)
                        
                        Attendance.objects.get_or_create(
                            employee_id=employee,
                            attendance_date=current_date,
                            defaults={
                                'attendance_clock_in': check_in,
                                'attendance_clock_out': check_out,
                                'attendance_worked_hour': f"{int(worked_hours):02d}:{int((worked_hours % 1) * 60):02d}",
                                'at_work': at_work,
                                'overtime_second': int(overtime * 3600),
                                'attendance_validated': True,
                                'is_validate_request': False,
                                'is_validate_request_approved': False,
                            }
                        )
                        attendance_count += 1
                
                current_date += timedelta(days=1)
        
        self.log(f"Created {attendance_count} attendance records for Sep & Oct 2025")
    
    def create_leave_data(self):
        """Create leave types, requests, and allocations"""
        if not apps.is_installed('leave'):
            self.log("Leave module not installed - skipping", 'warn')
            return
        
        self.header("Leave Data")
        
        # Create leave types
        leave_types_config = [
            ('Vacation Leave', 15, '#4CAF50', True),
            ('Sick Leave', 15, '#FF9800', True),
            ('Emergency Leave', 5, '#F44336', True),
            ('Maternity Leave', 105, '#E91E63', False),
            ('Paternity Leave', 7, '#2196F3', False),
        ]
        
        for name, days, color, is_compensatory in leave_types_config:
            leave_type, _ = LeaveType.objects.get_or_create(
                name=name,
                defaults={
                    'color': color,
                    'is_compensatory_leave': is_compensatory,
                    'total_days': days,
                    'reset': True,
                    'reset_based': 'yearly',
                    'carryforward_type': 'no carryforward',
                }
            )
            self.leave_types[name] = leave_type
        
        self.log(f"Created {len(self.leave_types)} leave types")
        
        # Create holidays
        holiday_count = 0
        for holiday_date, holiday_name in PH_HOLIDAYS_2025:
            Holiday.objects.get_or_create(
                start_date=holiday_date,
                defaults={
                    'name': holiday_name,
                    'end_date': holiday_date,
                    'recurring': True,
                }
            )
            holiday_count += 1
        
        self.log(f"Created {holiday_count} Philippine holidays")
        
        # Allocate leaves and create requests
        request_count = 0
        allocation_count = 0
        
        for employee in self.employees:
            # Allocate leave balances
            for leave_type_name, leave_type in self.leave_types.items():
                if leave_type.is_compensatory_leave:
                    # Give some used and available balance
                    available = random.randint(5, leave_type.total_days)
                    AvailableLeave.objects.get_or_create(
                        leave_type_id=leave_type,
                        employee_id=employee,
                        defaults={
                            'available_days': available,
                            'carryforward_days': 0,
                            'total_leave_days': leave_type.total_days,
                        }
                    )
                    allocation_count += 1
            
            # Create some leave requests (30% of employees)
            if random.random() < 0.3:
                # Random leave type
                leave_type = random.choice(list(self.leave_types.values()))
                
                # Random date in Sept or Oct
                if random.random() < 0.5:
                    start = date(2025, 9, random.randint(1, 28))
                else:
                    start = date(2025, 10, random.randint(1, 28))
                
                # Duration 1-3 days
                duration = random.randint(1, 3)
                end = start + timedelta(days=duration - 1)
                
                # Status
                status = random.choice(['approved', 'approved', 'approved', 'pending', 'rejected'])
                
                LeaveRequest.objects.get_or_create(
                    employee_id=employee,
                    leave_type_id=leave_type,
                    start_date=start,
                    end_date=end,
                    defaults={
                        'requested_days': duration,
                        'description': random.choice([
                            'Personal matters',
                            'Family emergency',
                            'Medical appointment',
                            'Rest and relaxation',
                            'Important family event'
                        ]),
                        'status': status,
                    }
                )
                request_count += 1
        
        self.log(f"Created {allocation_count} leave allocations and {request_count} leave requests")
    
    def create_asset_data(self):
        """Create assets and assignments"""
        if not apps.is_installed('asset'):
            self.log("Asset module not installed - skipping", 'warn')
            return
        
        self.header("Asset Data")
        
        # Asset categories
        categories = [
            'Laptop', 'Monitor', 'Keyboard', 'Mouse', 
            'Headset', 'Mobile Phone', 'Webcam'
        ]
        
        for cat_name in categories:
            cat, _ = AssetCategory.objects.get_or_create(
                asset_category_name=cat_name
            )
            self.asset_categories[cat_name] = cat
        
        self.log(f"Created {len(self.asset_categories)} asset categories")
        
        # Create assets and assign to employees
        assignment_count = 0
        asset_count = 0
        
        laptop_brands = ['Dell Latitude', 'HP EliteBook', 'Lenovo ThinkPad', 'MacBook Pro', 'ASUS VivoBook']
        monitor_brands = ['Dell UltraSharp', 'LG', 'Samsung', 'ASUS', 'BenQ']
        
        for i, employee in enumerate(self.employees):
            # Each employee gets a laptop
            laptop_cat = self.asset_categories.get('Laptop')
            if laptop_cat:
                laptop = Asset.objects.create(
                    asset_name=f"{random.choice(laptop_brands)} - {i+1:03d}",
                    asset_category_id=laptop_cat,
                    asset_tracking_id=f"LT-{i+1:04d}",
                    asset_status='In use',
                    asset_purchase_date=date.today() - timedelta(days=random.randint(30, 730)),
                    asset_purchase_cost=random.randint(35000, 85000),
                )
                
                AssetAssignment.objects.create(
                    asset_id=laptop,
                    assigned_to_employee_id=employee,
                    assigned_date=employee.employee_work_info.date_joining if hasattr(employee, 'employee_work_info') else date.today(),
                    asset_status='In use',
                )
                asset_count += 1
                assignment_count += 1
            
            # 70% get a monitor
            if random.random() < 0.7:
                monitor_cat = self.asset_categories.get('Monitor')
                if monitor_cat:
                    monitor = Asset.objects.create(
                        asset_name=f"{random.choice(monitor_brands)} 24\" - {i+1:03d}",
                        asset_category_id=monitor_cat,
                        asset_tracking_id=f"MON-{i+1:04d}",
                        asset_status='In use',
                        asset_purchase_date=date.today() - timedelta(days=random.randint(30, 730)),
                        asset_purchase_cost=random.randint(8000, 18000),
                    )
                    
                    AssetAssignment.objects.create(
                        asset_id=monitor,
                        assigned_to_employee_id=employee,
                        assigned_date=employee.employee_work_info.date_joining if hasattr(employee, 'employee_work_info') else date.today(),
                        asset_status='In use',
                    )
                    asset_count += 1
                    assignment_count += 1
        
        self.log(f"Created {asset_count} assets with {assignment_count} assignments")
    
    def create_helpdesk_data(self):
        """Create helpdesk tickets"""
        if not apps.is_installed('helpdesk'):
            self.log("Helpdesk module not installed - skipping", 'warn')
            return
        
        self.header("Helpdesk Tickets")
        
        # Ticket types
        ticket_types_config = [
            'IT Support', 'HR Inquiry', 'Payroll Issue', 
            'Leave Request Help', 'System Access', 'Other'
        ]
        
        for tt_name in ticket_types_config:
            tt, _ = TicketType.objects.get_or_create(
                title=tt_name
            )
            self.ticket_types[tt_name] = tt
        
        self.log(f"Created {len(self.ticket_types)} ticket types")
        
        # Create tickets (20% of employees)
        ticket_count = 0
        ticket_titles = [
            'Cannot access payroll system',
            'Forgot my password',
            'Need laptop repair',
            'Attendance not recorded',
            'Leave balance incorrect',
            'How to file overtime?',
            'Government ID update needed',
            'Benefits inquiry',
            'VPN connection issues',
            'Email access problem',
        ]
        
        for employee in random.sample(self.employees, k=int(len(self.employees) * 0.2)):
            ticket_type = random.choice(list(self.ticket_types.values()))
            
            Ticket.objects.create(
                employee_id=employee,
                ticket_type_id=ticket_type,
                title=random.choice(ticket_titles),
                description=f"Hello, I need assistance with {ticket_type.title.lower()}. Please help.",
                priority=random.choice(['low', 'medium', 'high']),
                status=random.choice(['open', 'in_progress', 'resolved', 'closed']),
                created_at=datetime.now() - timedelta(days=random.randint(1, 60)),
            )
            ticket_count += 1
        
        self.log(f"Created {ticket_count} support tickets")
    
    def create_payroll_data(self):
        """Create allowances, deductions, and sample payslips"""
        self.header("Payroll Data")
        
        # Create allowances
        allowance_config = [
            ('Transportation Allowance', 2000, 'fixed', 'monthly'),
            ('Meal Allowance', 1500, 'fixed', 'monthly'),
            ('Communication Allowance', 1000, 'fixed', 'monthly'),
        ]
        
        for name, amount, rate_type, pay_frequency in allowance_config:
            Allowance.objects.get_or_create(
                title=name,
                defaults={
                    'company_id': self.company,
                    'amount': Decimal(str(amount)),
                    'rate_type': rate_type,
                    'pay_frequency': pay_frequency,
                    'is_taxable': True,
                    'is_fixed': True,
                }
            )
        
        self.log("Created allowances (Transportation, Meal, Communication)")
        
        # Create PH deductions
        deduction_config = [
            ('SSS Contribution', 'percentage', 'Philippines'),
            ('PhilHealth Contribution', 'percentage', 'Philippines'),
            ('Pag-IBIG Contribution', 'percentage', 'Philippines'),
            ('Withholding Tax', 'percentage', 'Philippines'),
        ]
        
        for name, rate_type, country in deduction_config:
            Deduction.objects.get_or_create(
                title=name,
                defaults={
                    'company_id': self.company,
                    'deduction_type': rate_type,
                    'country': country,
                    'is_fixed': False,
                    'is_pretax': True,
                }
            )
        
        self.log("Created PH deductions (SSS, PhilHealth, Pag-IBIG, Tax)")
        
        # Generate payslips for September (for 20 employees)
        payslip_count = 0
        allowances = list(Allowance.objects.filter(company_id=self.company))
        deductions = list(Deduction.objects.filter(company_id=self.company, country='Philippines'))
        
        for employee in self.employees[:20]:
            contract = Contract.objects.filter(employee_id=employee).first()
            if not contract:
                continue
            
            # September 1-15 payslip
            sept_1_start = date(2025, 9, 1)
            sept_1_end = date(2025, 9, 15)
            
            basic_pay = contract.wage / 2  # Semi-monthly
            allowance_total = sum([a.amount for a in allowances])
            gross_pay = basic_pay + allowance_total
            
            # Approximate deductions (15% of gross)
            deduction_total = gross_pay * Decimal('0.15')
            net_pay = gross_pay - deduction_total
            
            payslip_1 = Payslip.objects.create(
                employee_id=employee,
                start_date=sept_1_start,
                end_date=sept_1_end,
                pay_period='semi-monthly',
                basic_pay=basic_pay,
                gross_pay=gross_pay,
                net_pay=net_pay,
                status='paid',
                company_id=self.company,
            )
            payslip_1.allowance.set(allowances)
            payslip_1.deduction.set(deductions)
            payslip_count += 1
            
            # September 16-30 payslip
            sept_2_start = date(2025, 9, 16)
            sept_2_end = date(2025, 9, 30)
            
            payslip_2 = Payslip.objects.create(
                employee_id=employee,
                start_date=sept_2_start,
                end_date=sept_2_end,
                pay_period='semi-monthly',
                basic_pay=basic_pay,
                gross_pay=gross_pay,
                net_pay=net_pay,
                status='paid',
                company_id=self.company,
            )
            payslip_2.allowance.set(allowances)
            payslip_2.deduction.set(deductions)
            payslip_count += 1
        
        self.log(f"Generated {payslip_count} payslips for September 2025")
    
    def configure_philippines_system(self):
        """Activate PH payroll config"""
        self.header("Philippines Configuration")
        
        config, _ = PayrollCountryConfig.objects.get_or_create(
            country='Philippines',
            defaults={
                'is_active': True,
                'requires_region': True,
                'requires_tax_status': True,
                'has_mandatory_benefits': True,
                'mandatory_benefits_list': 'SSS, PhilHealth, Pag-IBIG',
            }
        )
        
        if not config.is_active:
            config.is_active = True
            config.save()
        
        self.log("Philippines payroll system activated")
    
    def print_summary(self):
        """Print completion summary"""
        print("\n" + "=" * 80)
        print("  ✓ PHILIPPINES DEMO DATA LOADED SUCCESSFULLY!")
        print("=" * 80)
        print(f"\n[SUMMARY]")
        print(f"   Company: {self.company.company}")
        print(f"   Employees: {len(self.employees)} (salaries: ₱25,000 - ₱250,000)")
        print(f"   Departments: {len(self.departments)}")
        print(f"   Positions: {len(self.positions)}")
        print(f"   Attendance: Sep & Oct 2025 (full months)")
        print(f"   Leave Requests: Created with approvals")
        print(f"   Assets: Laptops, monitors assigned")
        print(f"   Helpdesk: Support tickets created")
        print(f"   Payroll: September payslips generated")
        
        print(f"\n[LOGIN CREDENTIALS]")
        print(f"   Any employee can login with:")
        print(f"   Password: Demo@2025")
        print(f"\n   Sample usernames:")
        for emp in self.employees[:5]:
            print(f"   • {emp.employee_user_id.username}")
        
        print(f"\n[NEXT STEPS]")
        print(f"   1. Login with employee credentials")
        print(f"   2. Explore attendance, leaves, assets")
        print(f"   3. Check payroll and payslips")
        print(f"   4. View Philippines-specific features")
        
        print("\n" + "=" * 80 + "\n")
    
    def run(self):
        """Execute all data generation"""
        print("\n" + "=" * 80)
        print("  LOADING PHILIPPINES DEMO DATA")
        print("  This will take a few minutes...")
        print("=" * 80)
        
        try:
            # Wrap entire operation in atomic transaction
            # If any signal hits missing table, rollback everything
            with transaction.atomic():
                self.create_company_and_structure()
                self.create_philippines_regions()
                self.create_employees()
                self.create_attendance_data()
                self.create_leave_data()
                self.create_asset_data()
                self.create_helpdesk_data()
                self.create_payroll_data()
                self.configure_philippines_system()
                self.print_summary()
            return True
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            print("Transaction rolled back - no partial data saved")
            import traceback
            traceback.print_exc()
            return False


def load_philippines_demo(num_employees=40):
    """Entry point for loading PH demo data"""
    generator = PhilippinesComprehensiveDemo(num_employees=num_employees)
    return generator.run()


if __name__ == '__main__':
    import sys
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    success = load_philippines_demo(num)
    sys.exit(0 if success else 1)
