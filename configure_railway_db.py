"""
Railway Database URL Configuration Helper
This script helps you set up the DATABASE_URL for Railway PostgreSQL sync.
"""

import os
import sys

def main():
    print("=" * 80)
    print("Railway DATABASE_URL Configuration")
    print("=" * 80)
    print()
    print("To sync your SQLite database to Railway PostgreSQL, you need the DATABASE_URL.")
    print()
    print("Steps to get your DATABASE_URL:")
    print("1. Go to your Railway project dashboard")
    print("2. Click on your PostgreSQL service")
    print("3. Go to the 'Variables' tab")
    print("4. Find 'DATABASE_URL' in the list")
    print("5. Copy the entire URL")
    print()
    print("The URL should look like:")
    print("postgresql://postgres:password@region.railway.app:5432/railway")
    print()
    print("-" * 80)
    
    database_url = input("Paste your Railway DATABASE_URL here: ").strip()
    
    if not database_url:
        print("\n❌ No URL provided. Exiting.")
        return False
        
    if not database_url.startswith(('postgresql://', 'postgres://')):
        print("\n❌ Invalid DATABASE_URL. It should start with 'postgresql://' or 'postgres://'")
        return False
    
    # Validate URL format
    try:
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        
        if not all([parsed.hostname, parsed.port, parsed.username, parsed.password]):
            print("\n⚠️  Warning: URL seems incomplete. Make sure it includes:")
            print("   - Username")
            print("   - Password")
            print("   - Hostname")
            print("   - Port")
            
            proceed = input("\nDo you want to proceed anyway? (yes/no): ").lower()
            if proceed != 'yes':
                return False
    except Exception as e:
        print(f"\n⚠️  Could not parse URL: {e}")
        print("Proceeding anyway...")
    
    # Set environment variable for current session
    os.environ['DATABASE_URL'] = database_url
    
    # Create .env file
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    print(f"\n✅ DATABASE_URL set for current session")
    print(f"\nDo you want to save it to .env file? (yes/no)")
    print(f"   File location: {env_file}")
    
    save = input("Save? ").lower()
    
    if save == 'yes':
        try:
            with open(env_file, 'a', encoding='utf-8') as f:
                f.write(f"\nDATABASE_URL={database_url}\n")
            print(f"✅ DATABASE_URL saved to {env_file}")
        except Exception as e:
            print(f"❌ Error saving to .env: {e}")
    
    print("\n" + "=" * 80)
    print("Configuration Complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Run: python sync_databases.py")
    print("   OR")
    print("2. Set environment variable in PowerShell:")
    print(f'   $env:DATABASE_URL="{database_url}"')
    print()
    
    return True

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🚀 You can now run the sync script!")
    sys.exit(0 if success else 1)
