"""
Load Production Data - Management Command
This runs automatically on Railway deployment to load production data.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from pathlib import Path
import os

class Command(BaseCommand):
    help = 'Load production data into database (for Railway deployment)'

    def handle(self, *args, **options):
        self.stdout.write("="*80)
        self.stdout.write("Loading Production Data")
        self.stdout.write("="*80)
        
        # Look for production data file
        base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        data_file = base_dir / 'load_data' / 'production_data.json'
        
        if not data_file.exists():
            self.stdout.write(self.style.WARNING(
                f"ℹ️  Production data file not found: {data_file}"
            ))
            self.stdout.write("Skipping production data load.")
            return
        
        self.stdout.write(f"Found production data: {data_file}")
        size_mb = data_file.stat().st_size / (1024 * 1024)
        self.stdout.write(f"Size: {size_mb:.2f} MB")
        
        try:
            self.stdout.write("\nLoading data (this may take several minutes)...")
            call_command('loaddata', str(data_file), verbosity=2)
            
            self.stdout.write(self.style.SUCCESS("\n✅ Production data loaded successfully!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Failed to load production data: {e}"))
            self.stdout.write(self.style.WARNING("Continuing without production data..."))
