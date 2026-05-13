# ⚠️ Virtual Bank & Wallet (Active Development)

This project is currently under active development and is continuously evolving.

Features, architecture, database structure, admin workflows, and internal banking logic may change as the system grows.

The project is active development with the goal of simulatating a real-world banking platform, with a strong focus on:

* secure financial workflows
* deterministic account provisioning
* role-based access control (RBAC)
* transaction safety
* concurrency protection
* scalable banking architecture
* clean domain-driven design principles


---

# Virtual Bank & Wallet (Django + PostgreSQL)

This project is a **virtual banking simulation system** built with Django and PostgreSQL.

It includes:

* wallet functionality
* user management
* banking operations
* role-based administration
* sequential account provisioning
* internal access control workflows

The system is designed to simulate banking-style infrastructure and operational workflows in a controlled development environment.

---

# Table of Contents

- [Python Version Requirements](#python-version-requirements-important)
- [Project Setup](#project-setup)
- [Database Setup](#️-database-setup-postgresql--pgadmin)
- [Environment Variables](#environment-variables)
- [Run Migrations](#run-migrations)
- [Create Superuser](#-create-superuser)
- [Available Routes](#some-available-routes)
- [Troubleshooting](#-troubleshooting)
- [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
- [Creating Roles](#creating-roles)
- [Assigning Permissions to Roles](#assigning-permissions-to-roles)
- [Assigning Users to Roles](#assigning-users-to-roles)
- [Django Admin Access Requirement](#django-admin-access-requirement)
- [User Visibility and Security Filtering](#user-visibility-and-security-filtering)
- [Create Banks and Bank Accounts](#create-banks-and-bank-accounts)
- [Why Sequential Generation Is Used](#why-sequential-generation-is-used)
- [Why Random Generation Is Avoided](#why-random-generation-is-avoided)
- [Concurrency Safety](#concurrency-safety)
- [Allocation Architecture](#allocation-architecture)

---

# Python Version Requirements (IMPORTANT)

This project is tested and recommended with:

* Python **3.11 – 3.13.x**
* Python **3.14+ is not recommended yet** due to partial ecosystem support across Django dependencies and third-party packages

See the official Python downloads page:

https://www.python.org/downloads/

### Recommended Check Before Setup

```bash
python --version
```

---

# Project Setup

## 1. Clone the Repository

```bash
git clone https://github.com/EgbieAndersonUku1/full_stack_virtual-bank .
```

---

## 2. Create a Virtual Environment (IMPORTANT)

### Recommended (ensures correct Python version)

```bash
py -3.13 -m venv venv
```

If Python 3.13 is not installed:

```bash
py -3.12 -m venv venv
```

---

# Activate Virtual Environment

## Windows (PowerShell)

```bash
.\venv\Scripts\Activate.ps1
```

## Windows (CMD)

```bash
venv\Scripts\activate
```

## macOS / Linux

```bash
source venv/bin/activate
```

---

## 3. Upgrade pip (Recommended)

```bash
python -m pip install --upgrade pip
```

---

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🗄️ Database Setup (PostgreSQL + pgAdmin)

## Requirements

* Python 3.11–3.13
* PostgreSQL
* pgAdmin 4
* pip / virtualenv

---

# Install PostgreSQL & pgAdmin

1. Download pgAdmin:
   https://www.pgadmin.org/download/

2. Download PostgreSQL:
   https://www.postgresql.org/download/

3. Set the `postgres` password during installation

4. Restart the system if pgAdmin does not load correctly

---

# Create Database

Inside pgAdmin:

* Servers → PostgreSQL
* Right-click `Databases`
* Create → Database
* Name: `virtual_bank`
* Owner: `postgres`

---

# Environment Variables

Create a `.env` file:

```env
NAME=
USER=postgres
PASSWORD=
HOST=localhost
PORT=5432
```

⚠️ Never commit `.env` files to GitHub.

---

# Django Database Configuration

Configure `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': getenv("NAME"),
        'USER': getenv("USER"),
        'PASSWORD': getenv("PASSWORD"),
        'HOST': getenv("HOST"),
        'PORT': getenv("PORT"),
    }
}
```

---

# Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

# 👤 Create Superuser

```bash
python manage.py createsuperuser
```

---

# Open Two Terminals

## Terminal One — Run Django Server

```bash
python manage.py runserver
```

---

## Terminal Two — Run Django-Q

This allows background tasks such as email processing.

```bash
python manage.py qcluster
```

---

# Some Available Routes

* App:
  http://127.0.0.1:8000/

* Dashboard:
  http://127.0.0.1:8000/dashboard

* Terms:
  http://127.0.0.1:8000/terms-and-conditions

* Admin:
  http://127.0.0.1:8000/admin/

---

# 🧪 Troubleshooting

## ❌ Dependency or Import Errors

* Ensure the correct Python version is installed (3.11–3.13)
* Recreate the virtual environment

---

## ❌ Database Connection Failed

* Ensure PostgreSQL service is running
* Verify `.env` values

---

## ❌ Migration Issues

```bash
python manage.py migrate --run-syncdb
```

---

# 📌 Notes

* Django connects directly to PostgreSQL
* pgAdmin is only a graphical database management tool
* Always use environment variables for secrets
* Keep dependencies pinned for stability
* Recreate the virtual environment if the Python version changes

---

# Role-Based Access Control (RBAC)

The system includes a structured Role-Based Access Control (RBAC) implementation using Django Groups and Permissions.

This transforms the Django admin into a:

> role-aware banking-style internal access control system

with:

* role assignment
* permission mapping
* secure admin workflows
* user visibility restrictions
* internal administrative controls

---

# Creating Roles

As a superuser navigate to:

```text
Authentication and Authorisation → Groups
```

Then:

1. Click `Add group`
2. Enter a role name such as:
   * Admin
   * Teller
   * Support
   * Customer
3. Assign permissions to the role
4. Click save

The group now acts as a reusable system role.

---

# Assigning Permissions to Roles

Inside the group:

* Add permissions for relevant models
* Define what actions the role can perform

Example:

| Role | Example Permissions |
|---|---|
| Teller | View accounts, change accounts |
| Support | View customers |
| Admin | Full permissions |

Django permissions include:

* view
* add
* change
* delete

---

# Assigning Users to Roles

Navigate to:

```text
Groups → Users tab
```

Then:

1. Click `Add another User`
2. Select the user
3. Click save

This automatically assigns all permissions attached to the group to the selected user.

⚠️ It is important to save the group before configuring admin access for the user.

Without saving the user into the group first, the role permissions may not yet be attached to the user account, which can result in manually reassigning permissions later.

---

# Django Admin Access Requirement

For a user to access Django admin:

```python
is_staff = True
```

must be enabled.

To enable this:

1. Open the user account
2. Enable `is_staff`
3. Click save

Without this, the user will authenticate successfully but will not be authorised to access the admin interface.

Example:

```text
You are authenticated as <email>, but are not authorised to access this page.
```

---

# User Visibility and Security Filtering

Admin user selection is automatically filtered to:

* active users only
* unlocked users only
* staff-aware visibility restrictions

This prevents inactive or locked accounts from being assigned within sensitive workflows.

---

# Permission-Based Admin Visibility

Once a user has been assigned:

* a role (group permissions)
* `is_staff=True`

they can successfully login and access the Django admin interface.

However, users will only see:

* models
* admin pages
* actions
* workflows

that their assigned permissions allow them to access.

This means the admin interface dynamically changes depending on the user's assigned role and permissions.

Example:

| Role | Example Admin Visibility |
|---|---|
| Teller | Accounts and transaction-related models only |
| Support | Customer support related models only |
| Admin | Full administrative access |

This ensures that internal users only interact with the parts of the system required for their operational responsibilities set to
them by the superuser.

The design is to ensure a secure and banking-style internal administration system built around the principle of:

> least privilege access control



# Create Banks and Bank Accounts

This project uses **sequential allocation** for both sort codes and account numbers.

The system intentionally avoids random number generation for financial identifiers.

---

# Why Sequential Generation Is Used

Sequential generation provides several guarantees required in banking and financial systems:

* predictable allocation boundaries
* collision prevention
* deterministic identifier issuance
* easier auditing and traceability
* efficient concurrency handling
* allocation integrity across banks

In this system, each bank receives an isolated allocation block.

All generated identifiers are issued sequentially within the assigned range.

Example:

```text
Bank A allocation block:
0 → 200000

Generated identifiers:

Sort Code:     000001
Account No:    00000001

Next:

Sort Code:     000002
Account No:    00000002
```

Another bank receives a different allocation range:

```text
Bank B allocation block:
200001 → 400000

Generated identifiers:

Sort Code:     200001
Account No:    00000001
```

This guarantees that identifier spaces never overlap between banks.

---

# Why Random Generation Is Avoided

The system intentionally avoids random generation because banking systems require strong guarantees around:

* uniqueness
* traceability
* allocation safety
* deterministic provisioning

Example of avoided approach:

```python
random.randint(0, 9999999)
```

Random generation introduces risks such as:

* collision handling complexity
* retry logic during concurrency
* fragmented identifier spaces
* reduced auditability
* non-deterministic allocation behaviour

Sequential allocation provides a safer and more predictable approach.

---

# Concurrency Safety

Identifier generation is protected using:

* database transactions
* row-level locking (`select_for_update`)

This prevents race conditions during concurrent account creation.

Guarantees include:

* no duplicate identifiers
* consistent allocation state
* atomic account creation workflows

---

# Allocation Architecture

The allocation system is composed of several domain components:

| Component | Responsibility |
|---|---|
| `SortCodeAllocationState` | Tracks global allocation progress |
| `SortCodeRangePool` | Stores reusable allocation ranges |
| `SortCode` | Tracks per-bank issued identifiers |
| `BankProvisioningService` | Creates and provisions banks |
| `AccountService` | Safely provisions bank accounts |

This architecture helps maintain strict allocation integrity while supporting scalability and concurrency safety.