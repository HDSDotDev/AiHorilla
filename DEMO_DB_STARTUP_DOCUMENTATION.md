**Overview**

This document explains what happens at application startup from the login screen and describes the two special actions shown on the login page when the application detects an uninitialized database:

- "Initialize Database" — interactive UI that walks the operator through creating the initial admin user/company.
- "Load Demo Data" — starts a background demo-data import tailored for either local SQLite (ORM generator) or PostgreSQL (clear+populate or JSON import).

**Files & locations**

- Login template: [templates/login.html](templates/login.html#L1-L500)
- Demo authentication modal: [templates/demo_database/auth_load_data.html](templates/demo_database/auth_load_data.html#L1-L120)
- Demo loader (SQLite/ORM generator): [load_philippines_demo.py](load_philippines_demo.py#L1-L40)
- Postgres-targeted demo loader: [load_philippines_demo_postgres.py](load_philippines_demo_postgres.py#L1-L120)
- Railway JSON import (SQLite dump -> Postgres): [railway_import_data.py](railway_import_data.py#L1-L120)
- Entrypoint logic for deployments: [entrypoint.sh](entrypoint.sh#L1-L120)
- Web handlers / URLs: [base/urls.py](base/urls.py#L1-L60), [base/views.py](base/views.py#L1-L120)

**When the login page shows the buttons**

The login page displays the two buttons only when the function `initialize_database_condition()` (in `base/views.py`) returns true. The heuristics used include:

- No users exist (no auth.User rows)
- No superuser with a linked `Employee` record
- Zero `Company` or `Employee` rows
- Missing expected payroll column checks (safety fallback)
- Presence of a `.railway_import_complete` flag combined with other checks

This conservative check ensures the operator sees initialization controls on an incomplete database.

**Initialize Database (button -> Initialize DB flow)**

Path: URL `initialize-database` -> `views.initialize_database` (see `base/views.py`)

Behavior summary:

- Presents an interactive web form to create an initial admin user (`initialize_database_user`) and then a company (`initialize_database_company`).
- The first POST to `initialize-database` requires `DB_INIT_PASSWORD` in settings to proceed; if correct, it redirects to the user creation step.
- The user creation step (`initialize_database_user`) creates/updates a Django `User` (superuser) and ensures an `Employee` record exists and is linked to the user. It also logs the user in and proceeds to company creation.
- Company creation and other initialization steps are implemented in subsequent `initialize_database_*` views (company, department, job positions etc.).

Primary security/config knobs:

- `DB_INIT_PASSWORD` (in `horilla_settings`) — used to authenticate operators on initialization forms.
- The `initialize_database_condition()` function decides whether to expose these actions.

**Load Demo Data (button -> Load demo flow)**

Path: URL `load-demo-database` -> `views.load_demo_database` (see `base/views.py`)

Top-level behavior:

- Only works when `initialize_database_condition()` is true (UI visible).
- The modal `templates/demo_database/auth_load_data.html` collects a `load_data_password` POST value which is checked against `DB_INIT_PASSWORD` before starting import.
- The handler detects the Django DB connection vendor and chooses the loader:
  - If `connection.vendor == 'postgresql'`: run `load_philippines_demo_postgres.py` (Postgres-targeted)
  - Otherwise: run `load_philippines_demo.py` (ORM-based generator, typically used for local SQLite)
- The loader is launched as a background subprocess so the HTTP request returns quickly; logs are written to `import_logs/` and a status file `.railway_import_running` is created.

Environment variables set/used by the loaders (when launched by the web UI):

- `SKIP_SCHEDULERS=1` — prevents background schedulers from running during import
- `DJANGO_DISABLE_AUDITLOG=1` — attempts to disable auditlog receivers to avoid extra DB writes
- `RAILWAY_IMPORT_CONFIRMED=true` — used by Postgres loader for non-interactive destructive operations

Files created by loader process:

- `import_logs/import_<timestamp>.out.log` and `import_logs/import_<timestamp>.err.log` — stdout/stderr
- `.railway_import_running` — short status file containing PID and log paths
- `/.railway_import_complete` — written on successful Postgres loader run (or by deployment scripts after import)

**SQLite (local dev) demo path — what gets populated**

When the site is using SQLite (or any non-postgres DB vendor), the web UI launches `load_philippines_demo.py`. This script is a full ORM generator and creates the following data (high level):

- Company
  - Company `BizBloqs BV Philippines` (address, country, city)
- Departments (typical company departments): Engineering, Product, Design, QA, Operations, Sales, Marketing, HR, Finance, Customer Support, IT
- Job Positions: a wide range (CTO, Engineering Manager, Senior Software Engineer, Software Engineer, etc.) mapped to departments
- Work types & Employee types (Full-time, Permanent)
- Shifts (e.g., "Day Shift (9AM-6PM)")
- Admin user + linked `Employee` record (username `admin`, password set to `admin` by script when needed)
- Philippine regions and minimum wage entries (region codes like NCR, CAR, Region III)
- Employees (~40 by default, configurable via CLI arg)
  - Realistic Filipino names from pools
  - Generated government IDs: TIN, SSS, PhilHealth, Pag-IBIG
  - Contact info, badge IDs, addresses, ph_region, ph_tax_status
  - EmployeeWorkInformation attached (company, position, dept, shift, joining date)
  - Contracts with wages (monthly, semi-monthly pay frequency)
  - Bank details
- Attendance records
  - Generated clock-in / clock-out for September & October 2025 for working days (mon–fri) with realistic check-in times and overtime where applicable
- Leave & Holidays
  - LeaveTypes (Vacation, Sick, Emergency, Maternity, Paternity) with allocations
  - PH holidays for 2025 added to Holidays table
  - Random LeaveRequest rows and AvailableLeave allocations
- Assets & Assignments
  - Asset categories (Laptop, Monitor, etc.), assets per employee, and AssetAssignment records
- Helpdesk tickets (sample tickets assigned to manager/admin employees)
- Payroll data
  - Allowances (Transportation, Meal, Communication)
  - Deductions (SSS, PhilHealth, Pag-IBIG, Withholding Tax)
  - Payslips generated (September semi-monthly payslips)
  - PayrollSettings and PayrollCountryConfig activated for Philippines (currency symbol ₱)
- Final prints a summary with example employee usernames and a shared demo password `Demo@2025` for created users

Notes on behavior and safety:

- The generator uses transactions (wraps most operations in `transaction.atomic()`), and prints rollback on exceptions to avoid partial imports.
- It monkey-patches `auditlog` receivers to no-op to prevent the audit app from failing if related tables are missing.
- The script writes outputs to STDOUT, which are captured in `import_logs` when launched from the web handler.

**PostgreSQL (production / Railway) demo path — what happens**

The web UI path for Postgres runs `load_philippines_demo_postgres.py`. That script:

1. Validates the DB engine is PostgreSQL.
2. In interactive mode it prompts for explicit confirmation; in non-interactive mode it requires `RAILWAY_IMPORT_CONFIRMED=true`.
3. Runs `call_command('flush', '--noinput')` followed by `call_command('migrate', '--noinput')` to clear the database and reapply migrations (destructive operation).
4. Calls into the same `load_philippines_demo` generator (the `load_philippines_demo.py` module) to populate data.
5. Writes `.railway_import_complete` on success.

Alternative Postgres import path used during deployments (entrypoint):

- During container startup on Railway the `entrypoint.sh` looks for a `full_database_dump.json` file. If present and `.railway_import_complete` is not set, the startup will run `railway_import_data.py` to import that JSON dump into PostgreSQL. That script:
  - Confirms PostgreSQL engine
  - Optionally clears DB (flush + migrate) with confirmation
  - Loads `full_database_dump.json` and performs a batched `bulk_create()` style import with heuristics to resolve FK references and many-to-many relations
  - Attempts to truncate long strings, resolve natural keys (username, email, code, slug, name) to PKs, and sets unresolved FKs to NULL (logging warnings)
  - Writes `.railway_import_complete` on success

So on a deployed Railway instance you may see either:

- JSON import via `railway_import_data.py` which restores a local SQLite snapshot (full_database_dump.json) into PostgreSQL preserving the exact objects present in the dump; OR
- The Postgres generator `load_philippines_demo_postgres.py` (clear+populate) which runs the same generator as local but after a destructive `flush`.

Which one runs is determined by deployment scripts and presence of `full_database_dump.json` in the repository/container.

**Key differences between SQLite (local) and PostgreSQL demo flows**

- SQLite/demo (web UI run) -> runs the ORM generator `load_philippines_demo.py` in-process (via a background subprocess) and does not forcibly flush the DB before running. It uses `transaction.atomic()` in the generator to avoid partial writes, but it will create new objects on top of existing rows.

- PostgreSQL/demo (web UI run) -> runs `load_philippines_demo_postgres.py`, which performs a destructive `flush` + `migrate` and then runs the same ORM generator to ensure a clean, consistent state. It requires `RAILWAY_IMPORT_CONFIRMED=true` for non-interactive runs.

- Railway deployment JSON import -> `railway_import_data.py` imports `full_database_dump.json` into Postgres and attempts to preserve the exact contents of the dump, using heuristics to resolve FKs and using `bulk_create` for speed.

**Operational notes / troubleshooting**

- Logs for web UI-initiated imports are in the repository `import_logs/` folder (created next to `manage.py`). Check the `.out.log`/.err.log files to follow progress.
- The web UI writes `.railway_import_running` with the PID + log paths. Presence of `.railway_import_complete` prevents re-running some import flows.
- If `load_philippines_demo_postgres.py` is used in production and fails during `flush`/`migrate`, the database can be left wiped — ensure backups (or `full_database_dump.json`) exist before running.
- The `railway_import_data.py` importer will set unresolved FK references to NULL and log warnings — inspect logs and run `python manage.py loaddata` type checks if needed.

**Quick locations summary**

- Login template & buttons: [templates/login.html](templates/login.html#L1-L500)
- Demo auth modal: [templates/demo_database/auth_load_data.html](templates/demo_database/auth_load_data.html#L1-L120)
- Web handler logic: [base/views.py](base/views.py#L1-L120) (`initialize_database_condition`, `load_demo_database`, `initialize_database`)
- SQLite/ORM generator: [load_philippines_demo.py](load_philippines_demo.py#L1-L40)
- Postgres destructive loader: [load_philippines_demo_postgres.py](load_philippines_demo_postgres.py#L1-L120)
- JSON dump importer: [railway_import_data.py](railway_import_data.py#L1-L120)
- Deployment entrypoint: [entrypoint.sh](entrypoint.sh#L1-L120)

**If you want, next steps**

- I can extract concrete examples (counts and sample records) from `full_database_dump.json` and attach a short CSV of created users/companies/employee usernames.
- Or I can add quick CLI commands to re-run the generators locally and capture timings/logs.

---

(Documentation generated by repository inspection on 2025-12-23)
