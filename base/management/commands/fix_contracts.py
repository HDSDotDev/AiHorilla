"""
Django management command to fix contract salaries and link job positions
"""
from django.core.management.base import BaseCommand
from payroll.models import Contract
from employee.models import EmployeeWorkInformation
from base.models import JobPosition
import random


class Command(BaseCommand):
    help = 'Fix contract salaries and link job positions for Philippines demo data'
    
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
    
    def get_salary_for_position(self, position_name):
        """Determine salary based on position title keywords"""
        position_lower = position_name.lower()
        
        # Check each salary range keyword
        for keyword, (min_sal, max_sal) in self.SALARY_RANGES.items():
            if keyword.lower() in position_lower:
                return random.randint(min_sal, max_sal)
        
        # Default for unmatched positions (mid-level range)
        return random.randint(35000, 55000)
    
    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write("  FIXING CONTRACTS & WORK INFO FOR PHILIPPINES DEMO DATA")
        self.stdout.write("="*80 + "\n")
        
        # First, assign job positions to all employees based on their badge ID
        self.stdout.write("\n[STEP 1] Assigning job positions to employees...")
        
        # Get all job positions
        positions = list(JobPosition.objects.all().order_by('id'))
        if not positions:
            self.stdout.write(self.style.ERROR("[ERROR] No job positions found!"))
            return
        
        self.stdout.write(f"[INFO] Found {len(positions)} job positions")
        
        # Get shifts and work types
        from base.models import EmployeeShift, WorkType
        shifts = list(EmployeeShift.objects.all())
        work_types = list(WorkType.objects.all())
        
        if not shifts:
            self.stdout.write(self.style.ERROR("[ERROR] No shifts found! Creating default shift..."))
            from base.models import Company
            company = Company.objects.first()
            shift = EmployeeShift.objects.create(
                employee_shift='Day Shift',
                shift_start_time='09:00:00',
                shift_end_time='18:00:00',
                company_id=company,
            )
            shifts = [shift]
        
        # Update all EmployeeWorkInformation with positions, shifts, and work types
        work_infos = EmployeeWorkInformation.objects.all()
        for work_info in work_infos:
            position = random.choice(positions)
            work_info.job_position_id = position
            work_info.department_id = position.department_id
            work_info.shift_id = random.choice(shifts) if shifts else None
            work_info.work_type_id = random.choice(work_types) if work_types else None
            work_info.save()
        
        self.stdout.write(self.style.SUCCESS(f"[OK] Updated {work_infos.count()} work info records with positions, shifts, and work types\n"))
        
        # Now fix contracts
        self.stdout.write("[STEP 2] Updating contract salaries...")
        
        contracts = Contract.objects.all()
        total = contracts.count()
        
        if total == 0:
            self.stdout.write(self.style.ERROR("[ERROR] No contracts found in database!"))
            return
        
        self.stdout.write(f"[INFO] Found {total} contracts to update\n")
        
        updated = 0
        failed = 0
        
        for contract in contracts:
            try:
                employee = contract.employee_id
                
                # Get job position from EmployeeWorkInformation (now it should have one)
                work_info = EmployeeWorkInformation.objects.filter(employee_id=employee).first()
                if not work_info or not work_info.job_position_id:
                    self.stdout.write(self.style.WARNING(
                        f"[WARN] No work info/position for {employee.employee_first_name}, skipping"
                    ))
                    failed += 1
                    continue
                
                position = work_info.job_position_id
                
                # Get appropriate salary for this position
                new_salary = self.get_salary_for_position(position.job_position)
                
                # Update contract with position info and salary
                contract.job_position = position
                contract.department = position.department_id
                contract.wage = float(new_salary)
                contract.contract_status = 'active'
                contract.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f"[OK] {employee.employee_first_name} {employee.employee_last_name:15} | "
                    f"{position.job_position:30} | PHP {new_salary:>9,}"
                ))
                
                updated += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"[ERROR] Failed to update contract {contract.id}: {str(e)}"
                ))
                failed += 1
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS(f"[SUCCESS] Updated {updated}/{total} contracts"))
        if failed > 0:
            self.stdout.write(self.style.WARNING(f"[WARNING] {failed} contracts failed to update"))
        self.stdout.write("="*80 + "\n")
