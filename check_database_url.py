"""
Railway Database URL Checker
This helps identify if you have the correct PUBLIC database URL
"""

import os
from urllib.parse import urlparse

print("\n" + "="*80)
print(" RAILWAY DATABASE_URL CHECKER ")
print("="*80 + "\n")

# Check current DATABASE_URL
db_url = os.environ.get('DATABASE_URL', '')

if not db_url:
    print("❌ No DATABASE_URL found in environment")
    print("\nPlease set it first:")
    print('   $env:DATABASE_URL="your-railway-url"')
else:
    print("Current DATABASE_URL:")
    print(f"   {db_url}\n")
    
    # Parse it
    try:
        parsed = urlparse(db_url)
        
        print("Parsed components:")
        print(f"   Scheme: {parsed.scheme}")
        print(f"   Username: {parsed.username}")
        print(f"   Password: {'*' * len(parsed.password or '')}")
        print(f"   Hostname: {parsed.hostname}")
        print(f"   Port: {parsed.port}")
        print(f"   Database: {parsed.path.lstrip('/')}")
        print()
        
        # Check if it's internal
        if '.railway.internal' in parsed.hostname:
            print("❌ PROBLEM DETECTED!")
            print("\nThis is an INTERNAL Railway hostname!")
            print(f"   Current: {parsed.hostname}")
            print("\nThe .railway.internal hostname only works INSIDE Railway containers,")
            print("not from your local machine.")
            print()
            print("="*80)
            print(" HOW TO FIX ")
            print("="*80)
            print("\n1. Go to Railway dashboard → Your PostgreSQL service")
            print("2. Click on the 'Connect' tab")
            print("3. Look for 'Public Networking' section")
            print("4. Copy the PUBLIC connection URL (it should have a .railway.app hostname)")
            print("\nOR")
            print("\n1. Go to Railway dashboard → Your PostgreSQL service")
            print("2. Click 'Settings' tab")
            print("3. Enable 'Public Networking' if not enabled")
            print("4. Use the public hostname (format: [region].railway.app)")
            print("\nThe URL should look like:")
            print("   postgresql://postgres:password@monorail.proxy.rlwy.net:12345/railway")
            print("   OR")
            print("   postgresql://postgres:password@region.railway.app:5432/railway")
            print()
            
        elif '.railway.app' in parsed.hostname or 'rlwy.net' in parsed.hostname:
            print("✅ This looks like a PUBLIC Railway URL!")
            print("\nYou should be able to connect from your local machine.")
            print("If connection still fails, check:")
            print("   1. Firewall settings")
            print("   2. Internet connection")
            print("   3. Railway service is running")
            
        else:
            print("⚠️  Unusual hostname format")
            print(f"   Hostname: {parsed.hostname}")
            print("\nFor Railway, the hostname should be either:")
            print("   - xxx.railway.app (public)")
            print("   - monorail.proxy.rlwy.net (public proxy)")
            print("   - xxx.railway.internal (internal only)")
            
    except Exception as e:
        print(f"❌ Error parsing URL: {e}")

print("\n" + "="*80)
print(" NEXT STEPS ")
print("="*80)
print("\n1. Get the CORRECT (public) DATABASE_URL from Railway")
print("2. Set it:")
print('   $env:DATABASE_URL="postgresql://postgres:pass@host:port/railway"')
print("3. Run sync again:")
print("   python sync_db_auto.py")
print()
