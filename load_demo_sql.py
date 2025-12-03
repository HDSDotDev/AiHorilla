#!/usr/bin/env python3
"""
Minimal SQL-based demo data loader
Bypasses Django ORM, signals, auditlog, and all middleware
Directly inserts data into PostgreSQL for maximum reliability
"""
import os
import sys
import psycopg2
from datetime import date, timedelta
import random
import hashlib
import base64

def make_password_hash(password, salt='demodata2025'):
    """
    Generate Django-compatible PBKDF2 SHA256 password hash
    Compatible with Django 4.2's password hashing
    """
    iterations = 600000  # Django 4.2 default
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                               salt.encode('utf-8'), iterations, dklen=32)
    hash_b64 = base64.b64encode(key).decode('ascii').strip()
    return f'pbkdf2_sha256${iterations}${salt}${hash_b64}'

def get_db_connection():
    """Get PostgreSQL connection from DATABASE_URL"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return None
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        return None

def load_minimal_demo_data():
    """Load minimal demo data using raw SQL"""
    print("=" * 80)
    print("LOADING MINIMAL DEMO DATA (SQL-based)")
    print("=" * 80)
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # 1. Create admin user if not exists
        print("\n[1/8] Creating admin user...")
        admin_password_hash = make_password_hash('admin')
        
        cur.execute("""
            INSERT INTO auth_user (password, last_login, is_superuser, username, first_name, 
                                   last_name, email, is_staff, is_active, date_joined)
            VALUES (%s, NULL, true, 'admin', 'Admin', 
                    'User', 'admin@example.com', true, true, NOW())
            ON CONFLICT (username) DO NOTHING
            RETURNING id;
        """, (admin_password_hash,))
        admin_result = cur.fetchone()
        if admin_result:
            admin_id = admin_result[0]
            print(f"  ✓ Admin user created (ID: {admin_id})")
        else:
            cur.execute("SELECT id FROM auth_user WHERE username='admin'")
            admin_id = cur.fetchone()[0]
            print(f"  ✓ Admin user exists (ID: {admin_id})")
        
        # 2. Create company FIRST (needed for employee work info)
        print("\n[2/8] Creating company...")
        cur.execute("""
            INSERT INTO base_company (company, address, country, state, city, zip, 
                                      icon, is_active, hq)
            VALUES ('BizBloqs Philippines', 'Manila, Philippines', 'Philippines', 
                    'Metro Manila', 'Manila', '1000', '', true, false)
            ON CONFLICT DO NOTHING
            RETURNING id;
        """)
        company_result = cur.fetchone()
        if company_result:
            company_id = company_result[0]
            print(f"  ✓ Company created (ID: {company_id})")
        else:
            cur.execute("SELECT id FROM base_company WHERE company='BizBloqs Philippines'")
            result = cur.fetchone()
            if result:
                company_id = result[0]
                print(f"  ✓ Company exists (ID: {company_id})")
        
        # Create admin employee record
        print("  - Creating admin employee record...")
        cur.execute("""
            INSERT INTO employee_employee (employee_user_id_id, employee_first_name, employee_last_name,
                                           email, phone, badge_id, is_active)
            VALUES (%s, 'Admin', 'User', 'admin@example.com', '000-000-0000', 'ADMIN001', true)
            ON CONFLICT (email) DO UPDATE SET employee_user_id_id = EXCLUDED.employee_user_id_id
            RETURNING id;
        """, (admin_id,))
        admin_emp_result = cur.fetchone()
        if admin_emp_result:
            admin_emp_id = admin_emp_result[0]
            print(f"  ✓ Admin employee created (ID: {admin_emp_id})")
        else:
            cur.execute("SELECT id FROM employee_employee WHERE email='admin@example.com'")
            result = cur.fetchone()
            if result:
                admin_emp_id = result[0]
                print(f"  ✓ Admin employee exists (ID: {admin_emp_id})")
        
        # Create EmployeeWorkInformation for admin (CRITICAL for CompanyMiddleware)
        print("  - Creating admin employee work information...")
        cur.execute("""
            INSERT INTO employee_employeeworkinformation (employee_id_id, company_id_id)
            VALUES (%s, %s)
            ON CONFLICT (employee_id_id) DO UPDATE SET company_id_id = EXCLUDED.company_id_id
            RETURNING employee_id_id;
        """, (admin_emp_id, company_id))
        work_info_result = cur.fetchone()
        if work_info_result:
            print(f"  ✓ Admin work info created (Employee: {work_info_result[0]})")
        else:
            print(f"  ⚠ Admin work info already exists")
        
        # 3. Create department
        print("\n[3/8] Creating department...")
        cur.execute("""
            INSERT INTO base_department (department, is_active)
            VALUES ('Engineering', true)
            ON CONFLICT DO NOTHING
            RETURNING id;
        """)
        dept_result = cur.fetchone()
        if dept_result:
            dept_id = dept_result[0]
            # Link department to company via ManyToMany junction table
            cur.execute("""
                INSERT INTO base_department_company_id (department_id, company_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;
            """, (dept_id, company_id))
            print(f"  ✓ Department created (ID: {dept_id})")
        else:
            cur.execute("SELECT id FROM base_department WHERE department='Engineering' LIMIT 1")
            result = cur.fetchone()
            dept_id = result[0] if result else None
            print(f"  ✓ Department exists (ID: {dept_id})")
        
        # 4. Create job position
        print("\n[4/8] Creating job position...")
        cur.execute("""
            INSERT INTO base_jobposition (job_position, department_id_id, is_active)
            VALUES ('Software Engineer', %s, true)
            ON CONFLICT DO NOTHING
            RETURNING id;
        """, (dept_id,))
        job_result = cur.fetchone()
        if job_result:
            job_id = job_result[0]
            # Link job position to company via ManyToMany junction table
            cur.execute("""
                INSERT INTO base_jobposition_company_id (jobposition_id, company_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;
            """, (job_id, company_id))
            print(f"  ✓ Job position created (ID: {job_id})")
        else:
            cur.execute("SELECT id FROM base_jobposition WHERE job_position='Software Engineer' LIMIT 1")
            result = cur.fetchone()
            job_id = result[0] if result else None
            print(f"  ✓ Job position exists (ID: {job_id})")
        
        # 5. Create shift
        print("\n[5/8] Creating employee shift...")
        cur.execute("""
            INSERT INTO base_employeeshift (employee_shift, weekly_full_time, full_time, is_active)
            VALUES ('Day Shift', '40:00', '200:00', true)
            ON CONFLICT DO NOTHING
            RETURNING id;
        """)
        shift_result = cur.fetchone()
        if shift_result:
            shift_id = shift_result[0]
            # Link shift to company via ManyToMany junction table
            cur.execute("""
                INSERT INTO base_employeeshift_company_id (employeeshift_id, company_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;
            """, (shift_id, company_id))
            print(f"  ✓ Shift created (ID: {shift_id})")
        else:
            cur.execute("SELECT id FROM base_employeeshift WHERE employee_shift='Day Shift' LIMIT 1")
            result = cur.fetchone()
            shift_id = result[0] if result else None
            print(f"  ✓ Shift exists (ID: {shift_id})")
        
        # 6. Create work type
        print("\n[6/8] Creating work type...")
        cur.execute("""
            INSERT INTO base_worktype (work_type, is_active)
            VALUES ('Full Time', true)
            ON CONFLICT DO NOTHING
            RETURNING id;
        """)
        worktype_result = cur.fetchone()
        if worktype_result:
            worktype_id = worktype_result[0]
            # Link work type to company via ManyToMany junction table
            cur.execute("""
                INSERT INTO base_worktype_company_id (worktype_id, company_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;
            """, (worktype_id, company_id))
            print(f"  ✓ Work type created (ID: {worktype_id})")
        else:
            cur.execute("SELECT id FROM base_worktype WHERE work_type='Full Time' LIMIT 1")
            result = cur.fetchone()
            worktype_id = result[0] if result else None
            print(f"  ✓ Work type exists (ID: {worktype_id})")
        
        # 7. Create employee type
        print("\n[7/8] Creating employee type...")
        cur.execute("""
            INSERT INTO base_employeetype (employee_type, is_active)
            VALUES ('Permanent', true)
            ON CONFLICT DO NOTHING
            RETURNING id;
        """)
        emptype_result = cur.fetchone()
        if emptype_result:
            emptype_id = emptype_result[0]
            # Link employee type to company via ManyToMany junction table
            cur.execute("""
                INSERT INTO base_employeetype_company_id (employeetype_id, company_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;
            """, (emptype_id, company_id))
            print(f"  ✓ Employee type created (ID: {emptype_id})")
        else:
            cur.execute("SELECT id FROM base_employeetype WHERE employee_type='Permanent' LIMIT 1")
            result = cur.fetchone()
            emptype_id = result[0] if result else None
            print(f"  ✓ Employee type exists (ID: {emptype_id})")
        
        # 8. Create 5 sample employees
        print("\n[8/8] Creating 5 sample employees...")
        employees = [
            ('Juan', 'Santos', 'juan.santos', 'juan.santos@example.com'),
            ('Maria', 'Reyes', 'maria.reyes', 'maria.reyes@example.com'),
            ('Pedro', 'Cruz', 'pedro.cruz', 'pedro.cruz@example.com'),
            ('Ana', 'Garcia', 'ana.garcia', 'ana.garcia@example.com'),
            ('Jose', 'Mendoza', 'jose.mendoza', 'jose.mendoza@example.com'),
        ]
        
        employee_ids = []
        for first_name, last_name, username, email in employees:
            # Create user with password "Demo@2025"
            employee_password_hash = make_password_hash('Demo@2025', salt=username)
            
            cur.execute("""
                INSERT INTO auth_user (password, last_login, is_superuser, username, first_name, 
                                       last_name, email, is_staff, is_active, date_joined)
                VALUES (%s, NULL, false, %s, %s, 
                        %s, %s, false, true, NOW())
                ON CONFLICT (username) DO NOTHING
                RETURNING id;
            """, (employee_password_hash, username, first_name, last_name, email))
            user_result = cur.fetchone()
            if user_result:
                user_id = user_result[0]
            else:
                cur.execute("SELECT id FROM auth_user WHERE username=%s", (username,))
                user_id = cur.fetchone()[0]
            
            # Create employee
            badge_id = f"EMP{1000 + len(employee_ids) + 1}"
            cur.execute("""
                INSERT INTO employee_employee (employee_user_id_id, employee_first_name, employee_last_name,
                                               email, phone, address, country, state, city, zip,
                                               dob, gender, qualification, experience, marital_status,
                                               children, emergency_contact, emergency_contact_name,
                                               emergency_contact_relation, is_active, badge_id)
                VALUES (%s, %s, %s, %s, '+63-XXX-XXXX', 'Manila', 'Philippines', 'Metro Manila', 
                        'Manila', '1000', '1990-01-01', 'male', 'Bachelor', 5, 'single', 0,
                        '+63-XXX-XXXX', 'Emergency Contact', 'family', true, %s)
                ON CONFLICT DO NOTHING
                RETURNING id;
            """, (user_id, first_name, last_name, email, badge_id))
            emp_result = cur.fetchone()
            if emp_result:
                emp_id = emp_result[0]
                employee_ids.append(emp_id)
                
                # Create employee work information
                cur.execute("""
                    INSERT INTO employee_employeeworkinformation 
                        (employee_id_id, job_position_id_id, department_id_id, work_type_id_id,
                         employee_type_id_id, shift_id_id, company_id_id, location, 
                         email, mobile, reporting_manager_id_id, date_joining, 
                         contract_end_date, basic_salary, salary_hour)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Manila Office', %s, '+63-XXX-XXXX',
                            NULL, '2025-01-01', NULL, 50000, 0)
                    ON CONFLICT DO NOTHING;
                """, (emp_id, job_id, dept_id, worktype_id, emptype_id, shift_id, company_id, email))
                
                print(f"  ✓ Employee created: {first_name} {last_name} (ID: {emp_id})")
            else:
                print(f"  ✓ Employee exists: {first_name} {last_name}")
        
        conn.commit()
        print("\n" + "=" * 80)
        print("✓ DEMO DATA LOADED SUCCESSFULLY")
        print("=" * 80)
        print(f"\nCreated:")
        print(f"  - Company: BizBloqs Philippines")
        print(f"  - Department: Engineering")
        print(f"  - Job Position: Software Engineer")
        print(f"  - {len(employee_ids)} Employees")
        print(f"\nLogin:")
        print(f"  - Username: admin / Password: admin")
        print(f"  - Or any employee username with password: Demo@2025")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    success = load_minimal_demo_data()
    sys.exit(0 if success else 1)
