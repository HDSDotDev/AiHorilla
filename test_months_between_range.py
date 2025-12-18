"""
Test months_between_range directly with September 2025
"""
import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from payroll.methods.methods import months_between_range

def test_months_function():
    """Test the months_between_range function"""
    
    print("\n" + "="*70)
    print("TESTING months_between_range() FUNCTION")
    print("="*70)
    
    test_cases = [
        {
            'name': 'September 2025 (full month)',
            'wage': 50000.0,
            'start': date(2025, 9, 1),
            'end': date(2025, 9, 30),
        },
        {
            'name': 'October 2025 (full month)',
            'wage': 50000.0,
            'start': date(2025, 10, 1),
            'end': date(2025, 10, 31),
        },
        {
            'name': 'November 2024 (past month)',
            'wage': 50000.0,
            'start': date(2024, 11, 1),
            'end': date(2024, 11, 30),
        },
        {
            'name': 'Invalid: end before start',
            'wage': 50000.0,
            'start': date(2025, 9, 30),
            'end': date(2025, 9, 1),
        },
    ]
    
    for test in test_cases:
        print(f"\n{'='*70}")
        print(f"TEST: {test['name']}")
        print(f"{'='*70}")
        print(f"Wage: PHP {test['wage']:,.2f}")
        print(f"Start: {test['start']}")
        print(f"End: {test['end']}")
        
        try:
            result = months_between_range(test['wage'], test['start'], test['end'])
            
            if not result:
                print("\n❌ RETURNED EMPTY LIST")
                print("This is the bug causing IndexError!")
            else:
                print(f"\n✅ SUCCESS - Returned {len(result)} month(s)")
                for month_data in result:
                    print(f"\nMonth {month_data['month']}/{month_data['year']}:")
                    print(f"  Working days in period: {month_data['working_days_on_period']}")
                    print(f"  Working days in month: {month_data['working_days_on_month']}")
                    print(f"  Per day amount: PHP {month_data['per_day_amount']:,.2f}")
                    print(f"  Start date: {month_data['start_date']}")
                    print(f"  End date: {month_data['end_date']}")
        
        except Exception as e:
            print(f"\n❌ EXCEPTION: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_months_function()
