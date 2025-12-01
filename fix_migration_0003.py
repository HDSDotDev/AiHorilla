#!/usr/bin/env python3
"""
Fix migration 0003 by removing all CreateModel operations.
All Philippine models already exist from migration 0001.
"""

import re

migration_file = "payroll/migrations/0003_payrollcountryconfig_philippinescola_and_more.py"

with open(migration_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the operations list start
operations_start = content.find('    operations = [')
if operations_start == -1:
    print("ERROR: Could not find operations list")
    exit(1)

# Find the first RemoveField operation
first_removefield = content.find('        migrations.RemoveField(', operations_start)
if first_removefield == -1:
    print("ERROR: Could not find RemoveField operations")
    exit(1)

# Extract everything before operations
before_operations = content[:operations_start]

# Extract everything from first RemoveField onward
after_createmodels = content[first_removefield:]

# Reconstruct the file
new_content = before_operations + '''    operations = [
        # NOTE: All Philippine models already created in migration 0001_initial.py
        # This migration only cleans up temporary models from migration 0002
        # and adds the 'region' field to philippinescola
        
        ''' + after_createmodels

with open(migration_file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✓ Migration 0003 fixed successfully")
print(f"  Removed all CreateModel operations")
print(f"  Kept RemoveField and DeleteModel operations for 0002 cleanup")
print(f"  Kept AddField operation for philippinescola.region")
