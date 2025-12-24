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
import hashlib

# Setup Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')

# Skip schedulers during demo data loading to prevent queries on potentially missing tables
os.environ['SKIP_SCHEDULERS'] = '1'

# Disable auditlog during demo data loading to prevent it from querying missing related tables
os.environ['DJANGO_DISABLE_AUDITLOG'] = '1'

django.setup()

# Deterministic seeding for demo data generation
try:
    seed_val = os.environ.get('DEMO_DATA_SEED')
    if seed_val is not None:
        try:
            seed_int = int(seed_val)
        except Exception:
            # Fallback: hash the string into an int
            seed_int = int(hashlib.sha256(seed_val.encode('utf-8')).hexdigest(), 16) % (2 ** 32)
        random.seed(seed_int)
        try:
            import numpy as _np

            _np.random.seed(seed_int)
        except Exception:
            # numpy not available — continue
            pass
        print(f"[DEMO LOADER] Using deterministic seed: {seed_int}")
    else:
        print("[DEMO LOADER] No DEMO_DATA_SEED provided — running non-deterministic generation")
except Exception as e:
    print(f"[DEMO LOADER] Seed initialization failed: {e}")

# After django.setup(), completely disable auditlog by monkey-patching the receiver
try:
    import auditlog.receivers
    # Replace the log creation functions with no-ops
    auditlog.receivers.log_create = lambda *args, **kwargs: None
    auditlog.receivers.log_update = lambda *args, **kwargs: None
    auditlog.receivers.log_delete = lambda *args, **kwargs: None
    print("[OK] Auditlog disabled for demo data loading")
except Exception as e:
    print(f"Note: Could not disable auditlog: {e}")

from django.contrib.auth.models import User
from django.db import transaction, connection
from django.apps import apps


def table_exists(table_name: str) -> bool:
    """Return True if the given DB table exists for the current connection.

    Uses Django's introspection where available and falls back to a quick
    `to_regclass` query for PostgreSQL. Exceptions are swallowed and False
    is returned on error to avoid crashing the demo loader during startup.
    """
    try:
        return table_name in connection.introspection.table_names()
    except Exception:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT to_regclass(%s);", [table_name])
                row = cursor.fetchone()
                return bool(row and row[0])
        except Exception:
            return False

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

# Helpdesk models (if installed and tables present)
if apps.is_installed('helpdesk') and table_exists('helpdesk_ticket'):
    from helpdesk.models import Ticket, TicketType, FAQ
else:
    print("[DEMO LOADER] helpdesk app not installed or helpdesk tables missing; skipping helpdesk model imports")

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
        self.fake_request = None
        self._setup_fake_request()
        
    def _setup_fake_request(self):
        """Setup fake request object for models that require it"""
        import horilla.horilla_middlewares as horilla_middlewares
        from django.contrib.auth.models import User
        
        # Get or create admin user for request.user
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@bizbloqs.ph',
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Admin',
                'last_name': 'User'
            }
        )
        if not admin_user.has_usable_password():
            admin_user.set_password('admin')
            admin_user.save()
        
        # Create Employee record for admin user (required to hide demo data button after load)
        from employee.models import Employee
        admin_employee, _ = Employee.objects.get_or_create(
            employee_user_id=admin_user,
            defaults={
                'employee_first_name': 'Admin',
                'employee_last_name': 'User',
                'email': 'admin@bizbloqs.ph',
                'phone': '+63-999-999-9999',  # Required field
                'badge_id': 'ADMIN-001',
                'is_active': True,
            }
        )
        
        # Create fake request object with minimal required attributes
        class FakeRequest:
            def __init__(self, user):
                self.user = user
                self.session = {}
                self.META = {}
                self.GET = {}
                self.POST = {}
        
        # Store it in thread locals where Horilla expects it
        horilla_middlewares._thread_locals.request = FakeRequest(admin_user)
    
    def log(self, message, level='info'):
        """Print formatted log message (Windows-compatible ASCII)"""
        symbols = {'info': '[OK]', 'warn': '[WARN]', 'error': '[ERROR]', 'step': '>>'}
        symbol = symbols.get(level, '-')
        print(f"   {symbol} {message}")
    
    def header(self, title):
        """Print section header"""
        print(f"\n[{title.upper()}]")
    
    def setup_fake_request(self):
        """Setup a fake request object for models that require it"""
        import horilla.horilla_middlewares as horilla_middlewares
        from types import SimpleNamespace
        from django.http import QueryDict
        
        # Create a fake user that passes all checks
        fake_user = SimpleNamespace()
        fake_user.is_authenticated = False
        fake_user.is_anonymous = True
        fake_user.username = 'system'
        fake_user.pk = None
        
        # Create a fake request with all required attributes
        self.fake_request = SimpleNamespace()
        self.fake_request.session = {}
        self.fake_request.user = fake_user
        self.fake_request.POST = QueryDict('', mutable=True)  # Empty POST data
        self.fake_request.GET = QueryDict('', mutable=True)   # Empty GET data
        self.fake_request.method = 'GET'
        
        # Set it in thread locals
        horilla_middlewares._thread_locals.request = self.fake_request
    
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
                # Check if exists first to avoid clean() method kwargs bug
                dept = Department.objects.filter(department=dept_name).first()
                if not dept:
                    dept = Department(department=dept_name)
                    dept.full_clean()
                    dept.save()
                # Add company if not already linked
                if not dept.company_id.filter(id=self.company.id).exists():
                    dept.company_id.add(self.company)
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
            work_type = WorkType.objects.filter(work_type='Full-time').first()
            if not work_type:
                work_type = WorkType(work_type='Full-time')
                work_type.save()
                work_type.company_id.add(self.company)
            elif not work_type.company_id.filter(id=self.company.id).exists():
                work_type.company_id.add(self.company)
            self.work_types.append(work_type)
            
            # Employee types
            emp_type = EmployeeType.objects.filter(employee_type='Permanent').first()
            if not emp_type:
                emp_type = EmployeeType(employee_type='Permanent')
                emp_type.save()
                emp_type.company_id.add(self.company)
            elif not emp_type.company_id.filter(id=self.company.id).exists():
                emp_type.company_id.add(self.company)
            self.employee_types.append(emp_type)
            
            # Create shift days (Monday-Friday)
            from base.models import EmployeeShiftDay
            for day_name in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
                day, _ = EmployeeShiftDay.objects.get_or_create(day=day_name)
                day.company_id.add(self.company)
            
            # Shifts
            day_shift = EmployeeShift.objects.filter(employee_shift='Day Shift (9AM-6PM)').first()
            if not day_shift:
                day_shift = EmployeeShift(employee_shift='Day Shift (9AM-6PM)')
                day_shift.save()
            self.shifts['day'] = day_shift
            
            self.log("Created work types, employee types, and shifts")
            
            # Update admin employee with work information
            from django.contrib.auth.models import User
            from employee.models import Employee, EmployeeWorkInformation
            try:
                admin_user = User.objects.get(username='admin')
                admin_employee = Employee.objects.get(employee_user_id=admin_user)
                
                # Get CEO position or create it
                ceo_position = self.positions.get('Chief Executive Officer')
                if not ceo_position:
                    ceo_dept = next((d for d in self.departments if d.department == 'Operations'), self.departments[0])
                    ceo_position, _ = JobPosition.objects.get_or_create(
                        job_position='Chief Executive Officer',
                        defaults={'department_id': ceo_dept}
                    )
                
                # Create/update work info for admin
                admin_work_info, _ = EmployeeWorkInformation.objects.get_or_create(
                    employee_id=admin_employee,
                    defaults={
                        'company_id': self.company,
                        'job_position_id': ceo_position,
                        'department_id': ceo_position.department_id,
                        'work_type_id': self.work_types[0] if self.work_types else None,
                        'employee_type_id': self.employee_types[0] if self.employee_types else None,
                        'shift_id': day_shift,
                        'email': 'admin@bizbloqs.ph',
                        'date_joining': date(2024, 1, 1),
                    }
                )
                self.log("Admin employee configured with work information")
            except (User.DoesNotExist, Employee.DoesNotExist):
                self.log("Admin employee setup skipped (not found)", level='warn')
    
    def create_philippines_regions(self):
        """Create PH regions"""
        self.header("Philippines Regions")
        
        for code, (name, wage) in REGIONS.items():
            region, _ = PhilippinesRegion.objects.get_or_create(
                region_code=code,
                defaults={
                    'region_name': name,
                    'daily_minimum_wage': Decimal(str(wage)),
                    'monthly_minimum_wage': Decimal(str(wage)) * 26,  # 26 working days
                    'effective_date': date(2024, 1, 1),  # Start of 2024
                    'company_id': self.company
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
                
                # Work information - use update_or_create to ensure all fields are set
                work_info, _ = EmployeeWorkInformation.objects.update_or_create(
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
                
                # Contract - create with full details
                contract = Contract.objects.filter(employee_id=employee).first()
                if not contract:
                    try:
                        contract = Contract(
                            employee_id=employee,
                            contract_name=f"{first_name} {last_name} - Employment Contract",
                            contract_start_date=hire_date,
                            contract_end_date=hire_date + timedelta(days=730),
                            wage=float(monthly_salary),  # FloatField expects float, not Decimal
                            wage_type='monthly',
                            pay_frequency='semi_monthly',
                            contract_status='active',  # Set to active to make it visible
                            department=position.department_id,
                            job_position=position,
                            shift=self.shifts.get('day'),
                            work_type=self.work_types[0] if self.work_types else None,
                        )
                        contract.save()
                    except Exception as e:
                        # If save fails, just print warning and continue
                        print(f"[WARN] Contract save issue for {username}: {str(e)[:50]}")
                
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
        
        self.log(f"Successfully created {len(self.employees)} employees with salaries ranging from PHP 25k to PHP 250k")
    
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
                        at_work_hours = min(worked_hours, 8.0)  # Standard 8 hours
                        overtime = max(0, worked_hours - 8.0)
                        
                        Attendance.objects.get_or_create(
                            employee_id=employee,
                            attendance_date=current_date,
                            defaults={
                                'shift_id': shift,
                                'attendance_clock_in_date': current_date,
                                'attendance_clock_in': check_in.time(),
                                'attendance_clock_out_date': current_date,
                                'attendance_clock_out': check_out.time(),
                                'attendance_worked_hour': f"{int(worked_hours):02d}:{int((worked_hours % 1) * 60):02d}",
                                'at_work_second': int(at_work_hours * 3600),
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
                        at_work_hours = min(worked_hours, 8.0)
                        overtime = max(0, worked_hours - 8.0)
                        
                        Attendance.objects.get_or_create(
                            employee_id=employee,
                            attendance_date=current_date,
                            defaults={
                                'shift_id': shift,
                                'attendance_clock_in_date': current_date,
                                'attendance_clock_in': check_in.time(),
                                'attendance_clock_out_date': current_date,
                                'attendance_clock_out': check_out.time(),
                                'attendance_worked_hour': f"{int(worked_hours):02d}:{int((worked_hours % 1) * 60):02d}",
                                'at_work_second': int(at_work_hours * 3600),
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
            leave_type = LeaveType.objects.filter(name=name).first()
            if not leave_type:
                # Set company_id to avoid save() method trying to access request.session
                leave_type = LeaveType(
                    name=name,
                    color=color,
                    is_compensatory_leave=is_compensatory,
                    total_days=days,
                    reset=True,
                    reset_based='yearly',
                    reset_month='1',  # January
                    reset_day='1',    # 1st day
                    carryforward_type='no carryforward',
                    company_id=self.company  # Set company_id to bypass session lookup
                )
                leave_type.save()
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
        
        # Use first employee (likely admin/manager) as the one assigning assets
        assigned_by = self.employees[0] if self.employees else None
        
        for i, employee in enumerate(self.employees):
            # Each employee gets a laptop
            laptop_cat = self.asset_categories.get('Laptop')
            if laptop_cat and assigned_by:
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
                    assigned_by_employee_id=assigned_by,
                    assigned_date=employee.employee_work_info.date_joining if hasattr(employee, 'employee_work_info') else date.today(),
                )
                asset_count += 1
                assignment_count += 1
            
            # 70% get a monitor
            if random.random() < 0.7:
                monitor_cat = self.asset_categories.get('Monitor')
                if monitor_cat and assigned_by:
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
                        assigned_by_employee_id=assigned_by,
                        assigned_date=employee.employee_work_info.date_joining if hasattr(employee, 'employee_work_info') else date.today(),
                    )
                    asset_count += 1
                    assignment_count += 1
        
        self.log(f"Created {asset_count} assets with {assignment_count} assignments")
    
    def create_helpdesk_data(self):
        """Create helpdesk tickets"""
        if not apps.is_installed('helpdesk'):
            self.log("Helpdesk module not installed - skipping", 'warn')
            return
        # Ensure the expected helpdesk tables exist before attempting ORM operations
        if not table_exists('helpdesk_ticket') or not table_exists('helpdesk_tickettype'):
            self.log("Helpdesk DB tables missing - skipping helpdesk demo data", 'warn')
            return
        
        self.header("Helpdesk Tickets")
        
        # Ticket types (title, type, prefix)
        ticket_types_config = [
            ('IT Support', 'service_request', 'IT'),
            ('HR Inquiry', 'service_request', 'HR'),
            ('Payroll Issue', 'complaint', 'PAY'),
            ('Leave Request Help', 'service_request', 'LVE'),
            ('System Access', 'service_request', 'SYS'),
            ('Other', 'others', 'OTH')
        ]
        
        for tt_name, tt_type, tt_prefix in ticket_types_config:
            tt, _ = TicketType.objects.get_or_create(
                title=tt_name,
                defaults={
                    'type': tt_type,
                    'prefix': tt_prefix,
                    'company_id': self.company
                }
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
        
        for employee in random.sample(self.employees, k=min(8, int(len(self.employees) * 0.2))):
            ticket_type = random.choice(list(self.ticket_types.values()))
            assigned_to = random.choice(self.employees[:5])  # Assign to first 5 employees (managers/admins)
            
            ticket = Ticket(
                employee_id=employee,
                ticket_type=ticket_type,
                title=random.choice(ticket_titles),
                description=f"Hello, I need assistance with {ticket_type.title.lower()}. Please help.",
                priority=random.choice(['low', 'medium', 'high']),
                assigning_type='employee',
                raised_on=str(assigned_to.pk),
            )
            ticket.save()
            ticket.assigned_to.add(assigned_to)
            ticket_count += 1
        
        self.log(f"Created {ticket_count} support tickets")
    
    def create_payroll_data(self):
        """Create allowances, deductions, and sample payslips"""
        self.header("Payroll Data")
        
        # Create allowances (manual creation to avoid save() bug)
        allowance_config = [
            ('Transportation Allowance', 2000),
            ('Meal Allowance', 1500),
            ('Communication Allowance', 1000),
        ]
        
        for name, amount in allowance_config:
            if not Allowance.objects.filter(title=name).exists():
                allowance = Allowance(
                    title=name,
                    company_id=self.company,
                    amount=float(amount),
                    is_taxable=True,
                    is_fixed=True,
                    include_active_employees=True,
                )
                allowance.save()
        
        self.log("Created allowances (Transportation, Meal, Communication)")
        
        # Create PH deductions (manual creation to avoid save() bug)
        deduction_config = [
            ('SSS Contribution', False),  # is_tax
            ('PhilHealth Contribution', False),
            ('Pag-IBIG Contribution', False),
            ('Withholding Tax', True),
        ]
        
        for name, is_tax in deduction_config:
            if not Deduction.objects.filter(title=name).exists():
                deduction = Deduction(
                    title=name,
                    company_id=self.company,
                    country='PH',
                    is_tax=is_tax,
                    is_pretax=True,
                    include_active_employees=True,
                )
                deduction.save()
        
        self.log("Created PH deductions (SSS, PhilHealth, Pag-IBIG, Tax)")
        
        # Generate payslips for September (for all employees)
        payslip_count = 0
        allowances = list(Allowance.objects.filter(company_id=self.company))
        deductions = list(Deduction.objects.filter(company_id=self.company, country='PH'))
        
        for employee in self.employees:
            contract = Contract.objects.filter(employee_id=employee).first()
            if not contract:
                continue
            
            # September 1-15 payslip
            sept_1_start = date(2025, 9, 1)
            sept_1_end = date(2025, 9, 15)
            
            basic_pay = Decimal(str(contract.wage)) / Decimal('2')  # Semi-monthly
            allowance_total = Decimal(str(sum([a.amount for a in allowances])))
            gross_pay = basic_pay + allowance_total
            
            # Approximate deductions (15% of gross)
            deduction_total = gross_pay * Decimal('0.15')
            net_pay = gross_pay - deduction_total
            
            # Pay head data includes all allowances and deductions
            pay_head_data = {
                'allowances': [{'title': a.title, 'amount': float(a.amount)} for a in allowances],
                'deductions': [{'title': d.title, 'amount': float(deduction_total / len(deductions))} for d in deductions]
            }
            
            payslip_1 = Payslip.objects.create(
                employee_id=employee,
                start_date=sept_1_start,
                end_date=sept_1_end,
                pay_head_data=pay_head_data,
                contract_wage=float(contract.wage),
                basic_pay=float(basic_pay),
                gross_pay=float(gross_pay),
                deduction=float(deduction_total),
                net_pay=float(net_pay),
                status='paid',
            )
            payslip_count += 1
            
            # September 16-30 payslip
            sept_2_start = date(2025, 9, 16)
            sept_2_end = date(2025, 9, 30)
            
            payslip_2 = Payslip.objects.create(
                employee_id=employee,
                start_date=sept_2_start,
                end_date=sept_2_end,
                pay_head_data=pay_head_data,
                contract_wage=float(contract.wage),
                basic_pay=float(basic_pay),
                gross_pay=float(gross_pay),
                deduction=float(deduction_total),
                net_pay=float(net_pay),
                status='paid',
            )
            payslip_count += 1
        
        self.log(f"Generated {payslip_count} payslips for September 2025")
    
    def configure_philippines_system(self):
        """Activate PH payroll config and set currency"""
        self.header("Philippines Configuration")
        
        # Set PayrollSettings currency to PHP
        from payroll.models import PayrollSettings
        payroll_settings, created = PayrollSettings.objects.get_or_create(
            company_id=self.company,
            defaults={
                'currency_symbol': '₱',
                'position': 'prefix',  # ₱ goes before amount
            }
        )
        if not created:
            payroll_settings.currency_symbol = '₱'
            payroll_settings.position = 'prefix'
            payroll_settings.save()
        
        self.log(f"Payroll currency {'set' if created else 'updated'} to Philippine Peso (PHP)")
        
        # Deactivate any active configs first
        PayrollCountryConfig.objects.filter(is_active=True, company_id=self.company).update(is_active=False)
        
        # Create or activate Philippines payroll config
        from django.contrib.auth.models import User
        admin_user = User.objects.filter(username='admin').first()
        admin_employee = Employee.objects.filter(employee_user_id=admin_user).first() if admin_user else None
        
        config, created = PayrollCountryConfig.objects.get_or_create(
            country='PH',
            company_id=self.company,
            defaults={
                'is_active': True,
                'activated_by': admin_employee,
            }
        )
        if not created:
            config.is_active = True
            config.activated_by = admin_employee
            config.save()
        
        self.log(f"Philippines payroll configuration {'created and ' if created else ''}activated (currency: PHP)")
        self.log("Philippines payroll system ready")
    
    def print_summary(self):
        """Print completion summary"""
        print("\n" + "=" * 80)
        print("  [SUCCESS] PHILIPPINES DEMO DATA LOADED SUCCESSFULLY!")
        print("=" * 80)
        print(f"\n[SUMMARY]")
        print(f"   Company: {self.company.company}")
        print(f"   Employees: {len(self.employees)} (salaries: PHP 25,000 - PHP 250,000)")
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
        
        # Debug: Print all users created
        from django.contrib.auth.models import User
        users = User.objects.all().values_list('username', 'is_superuser', 'is_staff')
        print(f"\n[DEBUG - ALL USERS CREATED]")
        for username, is_super, is_staff in users:
            print(f"   {username} (super:{is_super}, staff:{is_staff})")
        
        print("\n" + "=" * 80 + "\n")
    
    def run(self):
        """Execute all data generation"""
        print("\n" + "=" * 80)
        print("  LOADING PHILIPPINES DEMO DATA")
        print("  This will take a few minutes...")
        print("=" * 80)
        
        try:
            # Setup fake request for models that require it (like LeaveType)
            self.setup_fake_request()
            
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
