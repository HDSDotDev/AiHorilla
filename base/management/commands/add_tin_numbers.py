"""
Django management command to add TIN numbers to all employees
"""
from django.core.management.base import BaseCommand
from employee.models import Employee
import random


class Command(BaseCommand):
    help = 'Add TIN numbers to employees missing them'
    
    def generate_tin(self):
        """Generate a valid-looking Philippine TIN (xxx-xxx-xxx-xxx)"""
        return f"{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(100,999)}"
    
    def generate_sss(self):
        """Generate SSS number (xx-xxxxxxx-x)"""
        return f"{random.randint(10,99)}-{random.randint(1000000,9999999)}-{random.randint(0,9)}"
    
    def generate_philhealth(self):
        """Generate PhilHealth number (xx-xxxxxxxxx-x)"""
        return f"{random.randint(10,99)}-{random.randint(100000000,999999999)}-{random.randint(0,9)}"
    
    def generate_pagibig(self):
        """Generate Pag-IBIG number (xxxx-xxxx-xxxx)"""
        return f"{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
    
    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write("  ADDING PHILIPPINE GOVERNMENT IDs TO EMPLOYEES")
        self.stdout.write("="*80 + "\n")
        
        employees = Employee.objects.all()
        total = employees.count()
        
        if total == 0:
            self.stdout.write(self.style.ERROR("[ERROR] No employees found!"))
            return
        
        self.stdout.write(f"[INFO] Checking {total} employees\n")
        
        updated = 0
        
        for employee in employees:
            needs_update = False
            
            if not employee.tin_number:
                employee.tin_number = self.generate_tin()
                needs_update = True
            
            if not employee.sss_number:
                employee.sss_number = self.generate_sss()
                needs_update = True
            
            if not employee.philhealth_number:
                employee.philhealth_number = self.generate_philhealth()
                needs_update = True
            
            if not employee.pagibig_number:
                employee.pagibig_number = self.generate_pagibig()
                needs_update = True
            
            if needs_update:
                employee.save()
                self.stdout.write(self.style.SUCCESS(
                    f"[OK] {employee.employee_first_name} {employee.employee_last_name:15} | "
                    f"TIN: {employee.tin_number}"
                ))
                updated += 1
            else:
                self.stdout.write(
                    f"[SKIP] {employee.employee_first_name} {employee.employee_last_name} - already has IDs"
                )
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS(f"[SUCCESS] Updated {updated}/{total} employees"))
        self.stdout.write("="*80 + "\n")
