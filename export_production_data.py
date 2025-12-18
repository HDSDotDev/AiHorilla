"""
Export Production Data for Railway Deployment
Exports current SQLite data to a format that can be loaded during Railway deployment.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')

print("Initializing Django...")
django.setup()

from django.core.management import call_command
from pathlib import Path

def export_production_data():
    """Export all production data from SQLite"""
    print("\n" + "="*80)
    print(" EXPORTING PRODUCTION DATA ")
    print("="*80 + "\n")
    
    output_file = Path(__file__).parent / 'load_data' / 'production_data.json'
    output_file.parent.mkdir(exist_ok=True)
    
    print(f"Exporting to: {output_file}")
    print("This may take a few minutes...\n")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            call_command(
                'dumpdata',
                '--natural-foreign',
                '--natural-primary',
                '--exclude=contenttypes',
                '--exclude=auth.permission',
                '--exclude=sessions',  # Exclude session data
                '--indent=2',
                stdout=f,
                verbosity=1
            )
        
        size_mb = output_file.stat().st_size / (1024 * 1024)
        
        print("\n" + "="*80)
        print(f"✅ Export Complete!")
        print("="*80)
        print(f"File: {output_file}")
        print(f"Size: {size_mb:.2f} MB")
        print("\nThis file will be loaded on Railway during deployment.")
        print("\nNext steps:")
        print("1. Commit this file to git:")
        print(f"   git add {output_file.relative_to(Path.cwd())}")
        print("   git commit -m 'Add production data for Railway deployment'")
        print("2. Push to Railway:")
        print("   git push railway main")
        print("3. The deployment will automatically load this data.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = export_production_data()
    sys.exit(0 if success else 1)
