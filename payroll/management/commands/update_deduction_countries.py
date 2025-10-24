"""
Management command to update existing deductions with country information.
Sets Provident Fund, Professional Tax, and ESI as USA-specific deductions.
"""

from django.core.management.base import BaseCommand
from payroll.models.models import Deduction


class Command(BaseCommand):
    help = 'Updates existing deductions to set country field (USA for PF/PT/ESI)'

    def handle(self, *args, **options):
        self.stdout.write('Updating deductions with country information...')
        
        # USA-specific deductions
        usa_deduction_names = [
            'Provident Fund',
            'Professional Tax',
            'ESI',
            'Federal Tax',
            'State Tax',
            'Social Security',
            'Medicare',
        ]
        
        updated_count = 0
        for name in usa_deduction_names:
            deductions = Deduction.objects.filter(title__icontains=name)
            count = deductions.update(country='USA')
            if count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'  Updated {count} "{name}" deduction(s) to USA')
                )
                updated_count += count
        
        # Set all other deductions to GLOBAL (they'll work for all countries)
        global_deductions = Deduction.objects.filter(country='GLOBAL')
        global_count = global_deductions.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Complete! Updated {updated_count} USA-specific deductions'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'   {global_count} deductions remain as "All Countries"'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '\n⚠️  Next steps:'
            )
        )
        self.stdout.write('   1. Check Payroll → Deductions page')
        self.stdout.write('   2. Edit each deduction to set the correct country')
        self.stdout.write('   3. Generate new payslips to test filtering\n')
