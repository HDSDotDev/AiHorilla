#!/usr/bin/env python3
"""
Post-startup health check - verifies Gunicorn is responding
Run this separately after deployment to check if app is healthy
"""
import os
import sys
import time
import urllib.request
import urllib.error

port = os.environ.get('PORT', '8000')
url = f"http://localhost:{port}/"

print(f"Checking if application is responding on {url}...")

max_attempts = 30
for attempt in range(1, max_attempts + 1):
    try:
        print(f"Attempt {attempt}/{max_attempts}...", end=' ', flush=True)
        response = urllib.request.urlopen(url, timeout=5)
        print(f"✓ Got response: {response.status}")
        print(f"✓ Application is healthy and responding")
        sys.exit(0)
    except urllib.error.URLError as e:
        print(f"✗ {e}")
        if attempt < max_attempts:
            time.sleep(2)
        else:
            print(f"✗ Application not responding after {max_attempts} attempts")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)
