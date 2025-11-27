#!/usr/bin/env python
"""
PHILIPPINES PAYROLL DEMO DATA POPULATION SCRIPT

This script populates the database with realistic Philippine company data:
- BizBloqs BV company with PH operations
- 20 employees with complete PH government IDs
- Proper work info, contracts, and salary structures
- Sample payslips for the year
- Ready for PH payroll processing

Usage:
    python populate_philippines_demo.py
    
Options:
    --clear     Clear existing demo data before populating
    --employees N   Number of employees to create (default: 20)
"""

import os
import sys
import django
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

# Setup Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from employee.models import Employee, EmployeeWorkInformation, EmployeeBankDetails
from payroll.models.models import Contract, Payslip, Allowance, Deduction
from payroll.models.country_models import (
    PhilippinesRegion, 
    PhilippinesCOLA,
    PayrollCountryConfig
)
from base.models import Company, Department, JobPosition, WorkType, EmployeeShift, EmployeeType

# Philippine Demo Data Configuration
COMPANY_NAME = "BizBloqs BV"
COMPANY_TIN = "123-456-789-000"
COMPANY_ADDRESS = "Bonifacio Global City, Taguig, Metro Manila, Philippines"

# Philippine regions for demo
REGIONS = [
    'NCR', 'CAR', 'Region I', 'Region II', 'Region III', 
    'Region IV-A', 'Region IV-B', 'Region V'
]

# Tax statuses
TAX_STATUSES = ['S', 'S1', 'S2', 'S3', 'S4', 'ME', 'ME1', 'ME2', 'ME3', 'ME4']

# Job positions with salary ranges (monthly, in PHP)
POSITIONS = {
    'Software Engineer': (35000, 75000),
    'Senior Software Engineer': (60000, 120000),
    'Project Manager': (55000, 95000),
    'Business Analyst': (40000, 70000),
    'QA Engineer': (30000, 55000),
    'DevOps Engineer': (45000, 85000),
    'UX/UI Designer': (35000, 65000),
    'Data Analyst': (40000, 70000),
    'HR Specialist': (30000, 50000),
    'Accountant': (35000, 60000),
    'Administrative Assistant': (22000, 35000),
    'Sales Executive': (25000, 45000),
}

# Filipino names
FIRST_NAMES = [
    'Juan', 'Maria', 'Jose', 'Ana', 'Pedro', 'Rosa', 'Miguel', 'Carmen',
    'Antonio', 'Luz', 'Manuel', 'Elena', 'Francisco', 'Sofia', 'Carlos',
    'Isabel', 'Ramon', 'Teresa', 'Luis', 'Angelica', 'Ricardo', 'Patricia',
    'Gabriel', 'Michelle', 'Rafael', 'Christine', 'Fernando', 'Jennifer',
    'Eduardo', 'Angela', 'Daniel', 'Kristine', 'Roberto', 'Melissa'
]

LAST_NAMES = [
    'Santos', 'Reyes', 'Cruz', 'Bautista', 'Garcia', 'Mendoza', 'Torres',
    'Lopez', 'Gonzales', 'Flores', 'Rivera', 'Ramos', 'Gomez', 'Fernandez',
    'Sanchez', 'Ramirez', 'Castro', 'Aquino', 'Diaz', 'Morales', 'Hernandez',
    'Perez', 'Domingo', 'Villanueva', 'Mercado', 'Santiago', 'Navarro'
]


class PhilippinesDemoPopulator:
    """Populate database with Philippines-specific demo data"""
    
    def __init__(self, num_employees=20, clear_existing=False):
        self.num_employees = num_employees
        self.clear_existing = clear_existing
        self.company = None
        self.departments = []
        self.positions = []
        self.work_types = []
        self.shifts = []
        self.regions = []
        self.employees = []
        
    def print_header(self):
        print("\n" + "=" * 80)
        print("  PHILIPPINES PAYROLL - DEMO DATA POPULATION")
        print("  Company: BizBloqs BV (Philippines Operations)")
        print("=" * 80 + "\n")
    
    def clear_demo_data(self):
        """Clear existing demo data"""
        if not self.clear_existing:
            return
            
        print("[CLEAR] Clearing existing demo data...")  
        
        with transaction.atomic():
            # Delete in reverse dependency order
            Payslip.objects.all().delete()
            Contract.objects.all().delete()
            EmployeeBankDetails.objects.all().delete()
            EmployeeWorkInformation.objects.all().delete()
            
            # Don't delete users, just employees
            Employee.objects.all().delete()
            
            print("   ✓ Cleared employees, contracts, and payslips")
    
    def create_company_structure(self):
        """Create or get company, departments, positions"""
        print("[SETUP] Setting up company structure...")
        
        # Company
        self.company, created = Company.objects.get_or_create(
            company='BizBloqs BV',
            defaults={
                'address': COMPANY_ADDRESS,
                'country': 'Philippines',
                'state': 'Metro Manila',
                'city': 'Taguig',
                'zip': '1630',
            }
        )
        if created:
            print(f"   ✓ Created company: {self.company.company}")
        else:
            print(f"   ✓ Using existing company: {self.company.company}")
        
        # Departments - get existing or use first available
        self.departments = list(Department.objects.all()[:6])
        
        if not self.departments:
            print("   ⚠️  No departments found. Please create departments first.")
            print("      Continuing without departments...")
        
        if self.departments:
            print(f"   ✓ Using {len(self.departments)} existing departments")
        
        # Job Positions - get existing or create with existing departments
        self.positions = list(JobPosition.objects.all()[:12])
        
        if not self.positions and self.departments:
            # Create only if departments exist
            for position_name in list(POSITIONS.keys())[:5]:  # Create just 5 positions
                position, created = JobPosition.objects.get_or_create(
                    job_position=position_name,
                    defaults={'department_id': random.choice(self.departments)}
                )
                self.positions.append(position)
        
        if self.positions:
            print(f"   ✓ Using {len(self.positions)} job positions")
        else:
            print(f"   ⚠️  No job positions available")
        
        # Work Types - use existing
        self.work_types = list(WorkType.objects.all()[:1])
        if not self.work_types:
            print("   ⚠️  No work types found")
        else:
            print(f"   ✓ Using {len(self.work_types)} work type(s)")
        
        # Employee Types - use existing
        self.employee_types = list(EmployeeType.objects.all()[:1])
        if not self.employee_types:
            print("   ⚠️  No employee types found")
        else:
            print(f"   ✓ Using {len(self.employee_types)} employee type(s)")
        
        # Shifts - use existing
        self.shifts = list(EmployeeShift.objects.all()[:1])
        if not self.shifts:
            print("   ⚠️  No shifts found")
        else:
            print(f"   ✓ Using {len(self.shifts)} shift(s)")
    
    def create_philippines_regions(self):
        """Create Philippines regions if not exist"""
        print("[REGIONS] Setting up Philippines regions...")
        
        region_data = {
            'NCR': ('National Capital Region', 570.00),
            'CAR': ('Cordillera Administrative Region', 470.00),
            'Region I': ('Ilocos Region', 470.00),
            'Region II': ('Cagayan Valley', 470.00),
            'Region III': ('Central Luzon', 500.00),
            'Region IV-A': ('CALABARZON', 470.00),
            'Region IV-B': ('MIMAROPA', 435.00),
            'Region V': ('Bicol Region', 420.00),
        }
        
        for code, (name, wage) in region_data.items():
            region, created = PhilippinesRegion.objects.get_or_create(
                region_code=code,
                defaults={
                    'region_name': name,
                    'minimum_wage': Decimal(str(wage))
                }
            )
            self.regions.append(region)
        
        print(f"   ✓ Created/verified {len(self.regions)} regions")
    
    def generate_government_ids(self):
        """Generate realistic PH government IDs"""
        return {
            'tin': f"{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(0,9):03d}",
            'sss': f"{random.randint(10,99)}-{random.randint(1000000,9999999)}-{random.randint(0,9)}",
            'philhealth': f"{random.randint(10,99)}-{random.randint(100000000,999999999)}-{random.randint(0,9)}",
            'pagibig': f"{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
        }
    
    def create_employees(self):
        """Create employees with complete PH information"""
        print(f"[EMPLOYEES] Creating {self.num_employees} employees...")
        
        for i in range(self.num_employees):
            # Generate employee details
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            username = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,99)}"
            email = f"{username}@bizbloqs.ph"
            
            # Generate government IDs
            gov_ids = self.generate_government_ids()
            
            # Random position and salary
            if self.positions:
                position = random.choice(self.positions)
                position_name = position.job_position
                if position_name in POSITIONS:
                    salary_min, salary_max = POSITIONS[position_name]
                else:
                    salary_min, salary_max = 30000, 60000
            else:
                position = None
                salary_min, salary_max = 30000, 60000
            
            monthly_salary = random.randint(int(salary_min), int(salary_max))
            monthly_salary = round(monthly_salary / 1000) * 1000  # Round to nearest 1000
            
            # Random region and tax status
            region = random.choice(self.regions)
            tax_status = random.choice(TAX_STATUSES)
            
            # Hire date (random in last 2 years)
            days_ago = random.randint(30, 730)
            hire_date = date.today() - timedelta(days=days_ago)
            
            with transaction.atomic():
                # Create user
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                    }
                )
                if created:
                    user.set_password('Demo@123')  # Default password
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
                        'gender': random.choice(['male', 'female']),
                        'dob': date(random.randint(1985, 2000), random.randint(1, 12), random.randint(1, 28)),
                        'address': f"Unit {random.randint(1,50)}, {random.choice(['Makati', 'Taguig', 'Pasig', 'Quezon City'])}, Metro Manila",
                        'country': 'Philippines',
                        'state': 'Metro Manila',
                        'city': random.choice(['Makati', 'Taguig', 'Pasig', 'Quezon City', 'Manila']),
                        'is_active': True,
                        # Philippines-specific fields
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
                
                # Create work information
                work_info_defaults = {
                    'company_id': self.company,
                    'email': email,
                    'mobile': employee.phone,
                    'date_joining': hire_date,
                }
                
                if position:
                    work_info_defaults['job_position_id'] = position
                    work_info_defaults['department_id'] = position.department_id
                if self.work_types:
                    work_info_defaults['work_type_id'] = self.work_types[0]
                if self.employee_types:
                    work_info_defaults['employee_type_id'] = self.employee_types[0]
                if self.shifts:
                    work_info_defaults['shift_id'] = self.shifts[0]
                
                work_info, _ = EmployeeWorkInformation.objects.get_or_create(
                    employee_id=employee,
                    defaults=work_info_defaults
                )
                
                # Create contract
                contract, _ = Contract.objects.get_or_create(
                    employee_id=employee,
                    defaults={
                        'contract_name': f"{first_name} {last_name} - Employment Contract",
                        'contract_start_date': hire_date,
                        'contract_end_date': hire_date + timedelta(days=365*2),  # 2-year contract
                        'wage': Decimal(str(monthly_salary)),
                        'wage_type': 'monthly',
                    }
                )
                
                # Create bank details
                bank = EmployeeBankDetails.objects.create(
                    employee_id=employee,
                    bank_name=random.choice(['BDO', 'BPI', 'Metrobank', 'UnionBank', 'Security Bank']),
                    account_number=f"{random.randint(100000000000,999999999999)}",
                    any_other_code1=f"SWIFT{random.randint(1000,9999)}",
                )
                
                self.employees.append(employee)
            
            if (i + 1) % 5 == 0:
                print(f"   ✓ Created {i+1}/{self.num_employees} employees...")
        
        print(f"   ✓ Successfully created {len(self.employees)} employees")
    
    def create_sample_payslips(self):
        """Create sample payslips for the current year"""
        print("[PAYSLIPS] Generating sample payslips...")
        
        # Get existing allowances and deductions instead of creating
        allowances = list(Allowance.objects.filter(company_id=self.company)[:2])
        deductions = list(Deduction.objects.filter(company_id=self.company, country='Philippines')[:3])
        
        if not allowances or not deductions:
            print("   ⚠️  No allowances/deductions found - skipping payslips")
            return
        
        current_year = datetime.now().year
        months_to_generate = 6  # Last 6 months
        
        payslip_count = 0
        for employee in self.employees[:10]:  # Generate for first 10 employees only
            contract = Contract.objects.filter(employee_id=employee).first()
            if not contract:
                continue
            
            for month_offset in range(months_to_generate):
                # Calculate period dates
                period_end = date.today().replace(day=15) - timedelta(days=30*month_offset)
                if period_end.day > 15:
                    period_end = period_end.replace(day=15)
                else:
                    prev_month = period_end.replace(day=1) - timedelta(days=1)
                    period_end = prev_month.replace(day=15)
                
                period_start = period_end.replace(day=1)
                
                # Skip if already exists
                if Payslip.objects.filter(
                    employee_id=employee,
                    start_date=period_start,
                    end_date=period_end
                ).exists():
                    continue
                
                # Calculate semi-monthly pay
                basic_pay = contract.wage / 2  # Semi-monthly
                
                with transaction.atomic():
                    payslip = Payslip.objects.create(
                        employee_id=employee,
                        start_date=period_start,
                        end_date=period_end,
                        pay_period='semi-monthly',
                        basic_pay=basic_pay,
                        gross_pay=basic_pay + Decimal('3500.00'),  # Including allowances
                        net_pay=basic_pay * Decimal('0.85'),  # After deductions (approximate)
                        status='paid',
                        company_id=self.company,
                    )
                    
                    # Add available allowances and deductions
                    if allowances:
                        payslip.allowance.add(*allowances)
                    if deductions:
                        payslip.deduction.add(*deductions)
                    
                    payslip_count += 1
        
        print(f"   ✓ Generated {payslip_count} sample payslips")
    
    def configure_philippines_payroll(self):
        """Activate Philippines payroll configuration"""
        print("[CONFIG] Configuring Philippines payroll system...")
        
        config, created = PayrollCountryConfig.objects.get_or_create(
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
        
        print("   ✓ Philippines payroll system configured and activated")
    
    def print_summary(self):
        """Print summary of created data"""
        print("\n" + "=" * 80)
        print("  [SUCCESS] DEMO DATA POPULATION COMPLETE!")
        print("=" * 80)
        print(f"\n[SUMMARY]")
        print(f"   • Company: {self.company.company}")
        print(f"   • Departments: {len(self.departments)}")
        print(f"   • Job Positions: {len(self.positions)}")
        print(f"   • Employees: {len(self.employees)}")
        print(f"   • Philippines Regions: {len(self.regions)}")
        print(f"   • Sample Payslips: Generated for first 10 employees")
        
        print(f"\n[LOGIN] Credentials:")
        print(f"   Username: {self.employees[0].employee_user_id.username}")
        print(f"   Password: Demo@123")
        print(f"   (All demo users have the same password)")
        
        print(f"\n[DETAILS] Employee Sample:")
        for emp in self.employees[:5]:
            print(f"   • {emp.get_full_name()} ({emp.badge_id})")
            print(f"     TIN: {emp.tin_number}")
            print(f"     SSS: {emp.sss_number}")
            print(f"     Region: {emp.ph_region.region_name if emp.ph_region else 'N/A'}")
            print(f"     Tax Status: {emp.ph_tax_status}")
        
        if len(self.employees) > 5:
            print(f"   ... and {len(self.employees) - 5} more employees")
        
        print(f"\n[NEXT STEPS]")
        print(f"   1. Login with any employee credentials")
        print(f"   2. Navigate to Payroll > Philippines menu")
        print(f"   3. Try generating:")
        print(f"      - 13th Month Pay")
        print(f"      - BIR Form 2316")
        print(f"      - Final Pay calculations")
        print(f"      - Government remittance forms")
        
        print("\n" + "=" * 80 + "\n")
    
    def run(self):
        """Execute the population process"""
        self.print_header()
        
        try:
            self.clear_demo_data()
            self.create_company_structure()
            self.create_philippines_regions()
            self.create_employees()
            self.create_sample_payslips()
            self.configure_philippines_payroll()
            self.print_summary()
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Error during population: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Populate database with Philippines payroll demo data'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing demo data before populating'
    )
    parser.add_argument(
        '--employees',
        type=int,
        default=20,
        help='Number of employees to create (default: 20)'
    )
    
    args = parser.parse_args()
    
    populator = PhilippinesDemoPopulator(
        num_employees=args.employees,
        clear_existing=args.clear
    )
    
    success = populator.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
