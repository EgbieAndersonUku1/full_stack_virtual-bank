# ⚠️ Virtual Bank & Wallet (Active Development)

This project is currently under active development and is continuously evolving.

Features, architecture, database structure, admin workflows, and internal banking logic may change as the system grows.

The project is active development with the goal of simulatating a real-world banking platform, with a strong focus on:

- secure financial workflows

- deterministic account provisioning

- role-based access control (RBAC)

- transaction safety

- concurrency protection

- scalable banking architecture

- clean domain-driven design principles

---

# Virtual Bank & Wallet (Django + PostgreSQL)

This project is a **virtual banking simulation system** built with Django and PostgreSQL.

It includes:

- wallet functionality

- user management

- banking operations

- role-based administration

- sequential account provisioning

- internal access control workflows

The system is designed to simulate banking-style infrastructure and operational workflows in a controlled development environment.

---

# Table of Contents

- [Python Version Requirements](#python-version-requirements-important)

- [Project Setup](#project-setup)

- [Database Setup](#️-database-setup-postgresql--pgadmin)

- [Environment Variables](#environment-variables)

- [Run Migrations](#run-migrations)

- [Seed Demo Banking Data](#-seed-demo-banking-data)

- [Seed Banks](#seed-banks)

- [Reset Simulation Data](#reset-simulation-data)

- [Reseeding Workflow](#reseeding-workflow)

- [Static Logo Files](#static-logo-files)

- [Why Static Assets Are Used for Logos](#why-static-assets-are-used-for-logos)

- [Create Superuser](#-create-superuser)

- [Development Email Storage](#-development-email-storage)

- [Password Reset Security & Timing Attack Mitigation](#password-reset-security--timing-attack-mitigation)
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

- Python **3.11 – 3.13.x**

- Python **3.14+ is not recommended yet** due to partial ecosystem support across Django dependencies and third-party packages

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

- Python 3.11–3.13

- PostgreSQL

- pgAdmin 4

- pip / virtualenv

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

- Servers → PostgreSQL

- Right-click `Databases`

- Create → Database

- Name: `virtual_bank`

- Owner: `postgres`

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

## PostgreSQL Must Be Running

If the Django development server hangs after:

```

System check identified no issues (0 silenced).

```

and does not continue to:

```

Starting development server at http://127.0.0.1:8000/

```

then the most likely cause is that the PostgreSQL service is not running.

Django attempts to connect to the database during startup, and if the database is unavailable, the server may appear to freeze or fail to complete startup.

---

### Fix (Windows)

1. Press `Win + R`

2. Type:

```

services.msc

```

3. Locate **PostgreSQL**

4. Ensure the service is **Running**

   - If not, click **Start**

   - Or right-click → **Restart**

5. (Recommended) Set Startup Type to:

```

Automatic

```

---

### Quick Port Check

```bash

netstat -ano | findstr :5432

```

---

### Why this happens

Django connects to PostgreSQL during startup.

If the database is not running:

- migrations cannot be checked

- connection times out

- server startup halts

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

---

# Seed Demo Banking Data

This project includes management commands for seeding and resetting simulation banking data during development.

The seed command provisions demo banks using the internal banking allocation system.

This includes:

- banks

- sort code allocation ranges

- allocation state records

- provisioning metadata

⚠️ These commands are intended for development environments or testing simulations only.

---

# Seed Banks

Run the following command:

```bash

python manage.py seed_banks

```

This will create the predefined demo banks included with the project.

Example seeded data includes:

- digital banks

- investment banks

- mutual banks

- high-street banking simulations

The command uses the internal:

```python

BankProvisioningService

```

to ensure all required allocation and provisioning workflows are executed correctly.

---

# Reset Simulation Data

To clear simulation banking data during development:

```bash

python manage.py reset_simulations

```

This command removes simulation allocation records and seeded banking data so the environment can be reseeded cleanly.

Example cleanup includes:

- bank accounts

- sort codes

- allocation state records

- seeded banks

⚠️ This command should only be used in development or for running the simulation.

---

# Reseeding Workflow

Typical development workflow:

```bash

python manage.py reset_simulations

python manage.py seed_banks

```

This allows the banking simulation environment to be rebuilt from a clean state.

---

# Static Logo Files

Bank logos are stored as static assets.

Expected location:

```text

static/banks/logo/

```

Example:

```text

static/banks/logo/atlas-bank.png

```

The seed data references these static image paths directly.

---

# Why Static Assets Are Used for Logos

The project intentionally stores demo bank logos inside static assets instead of user-uploaded media files.

This ensures:

- cloned repositories work immediately

- seeded banks always have logo references

- contributors do not need manual media setup

- demo environments remain reproducible

This approach is intended for simulation and development workflows.

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

# 📧 Development Email Storage

Since this project is a **banking simulation environment**, emails are handled locally during development instead of being sent through an external email provider. This keeps the project self-contained and avoids requiring developers to configure an external email service while testing workflows.

This allows registration emails and other notifications generated by the application to be tested without requiring email service configuration.

After performing actions such as user registration or account-related workflows, generated emails can be found inside:

```text

send_emails/dev/

```

Example:

```text

send_emails/

└── dev/

    ├── welcome_email.log

    ├── verification_email.log

    └── account_notification.log

```

This approach keeps the development setup simple by:

- avoiding the need to configure external email services

- allowing developers to view generated emails locally

- making email workflows easier to test during development

In a production environment, emails would typically be delivered through a configured email service provider. This local email storage workflow is intended only for the simulated banking environment.

**Note:**

- The filenames shown above in the examples are simplified examples for readability. In the actual application, the backend controls email file naming and generates a unique random filename with a `.log` extension. To locate your email, check the latest generated file.

---

## Terminal Two — Run Django-Q

This allows background tasks such as email processing.

```bash

python manage.py qcluster

```

---

# Password Reset Security & Timing Attack Mitigation

The password reset functionality is designed to reduce the risk of **user enumeration through timing attacks**, while ensuring that email processing does not block the application.

## What is a timing attack?

A timing attack occurs when an attacker measures differences in application response times to infer information that should remain private.

For example, when a user requests a password reset, the application returns the same generic message regardless of whether the email address exists:

> If an account exists with this email address, a password reset link will be sent.

Although this prevents the application from explicitly revealing whether an account exists, the time taken to return the response may still expose that information.

Consider two scenarios:

**Scenario 1 — Email address exists**

1. The application searches for the email address.
2. The associated user is found.
3. A password reset token is generated.
4. A password reset email is prepared and sent.
5. The application returns a response.

**Scenario 2:  Email address does not exist**

1. The application searches for the email address.
2. No matching user is found.
3. The application returns a response.

The first scenario may take longer because additional operations are performed.

An attacker could repeatedly submit different email addresses and compare their response times. Over many requests, these differences may allow the attacker to infer which addresses are registered.

This is known as **timing-based user enumeration**.

Although discovering a registered email address does not directly compromise an account, it provides information that could be used in further attacks.

## How does the application mitigate this?

The application uses **Django-Q** to delegate password reset processing to an asynchronous background task.

Instead of performing account-dependent operations during the HTTP request, the application queues the work for background processing.

The intended workflow is:

1. A user submits their email address through the forgotten password form.
2. The application queues a background task using Django-Q.
3. The application returns the same generic response regardless of whether the email address exists in the same time which instantaneously.
4. The Django-Q worker processes the request independently.
5. If an eligible account exists, a password reset token is generated and an email is prepared for delivery.
6. If no eligible account exists, no reset email is generated.

By moving account-dependent operations into the background task, the application reduces differences in HTTP response times that could otherwise reveal whether an account exists.

This approach also improves the user experience because the application does not need to wait for email processing before responding.

**Important:** Asynchronous processing reduces timing-based information leakage but does not guarantee its elimination. The user lookup and other account-dependent operations must occur inside the background task for this mitigation to be effective.

## Current implementation status

The password reset functionality is currently under development.

The initial implementation introduces asynchronous request handling and a password reset page.

However:

- Password reset email delivery is not yet implemented.
- Password reset tokens are not yet validated.
- The reset page currently accepts arbitrary username and token values.
- Password updating through the reset link is not yet functional.

These features will be implemented in subsequent development stages.

---

# Some Available Routes

- App:

  http://127.0.0.1:8000/

- Dashboard:

  http://127.0.0.1:8000/dashboard

- Terms:

  http://127.0.0.1:8000/terms-and-conditions

- Admin:

  http://127.0.0.1:8000/admin/

---

# 🧪 Troubleshooting

## ❌ Dependency or Import Errors

- Ensure the correct Python version is installed (3.11–3.13)

- Recreate the virtual environment

---

## ❌ Database Connection Failed

- Ensure PostgreSQL service is running

- Verify `.env` values

---

## ❌ Migration Issues

```bash

python manage.py migrate --run-syncdb

```

---

# 📌 Notes

- Django connects directly to PostgreSQL

- pgAdmin is only a graphical database management tool

- Always use environment variables for secrets

- Keep dependencies pinned for stability

- Recreate the virtual environment if the Python version changes

---

# Role-Based Access Control (RBAC)

The system includes a structured Role-Based Access Control (RBAC) implementation using Django Groups and Permissions.

This transforms the Django admin into a:

> role-aware banking-style internal access control system

with:

- role assignment

- permission mapping

- secure admin workflows

- user visibility restrictions

- internal administrative controls

---

# Creating Roles

As a superuser navigate to:

```text

Authentication and Authorisation → Groups

```

Then:

1. Click `Add group`

2. Enter a role name such as:

   - Admin

   - Teller

   - Support

   - Customer

3. Assign permissions to the role

4. Click save

The group now acts as a reusable system role.

---

# Assigning Permissions to Roles

Inside the group:

- Add permissions for relevant models

- Define what actions the role can perform

Example:

\| Role    | Example Permissions            |

\| ------- | ------------------------------ |

\| Teller  | View accounts, change accounts |

\| Support | View customers                 |

\| Admin   | Full permissions               |

Django permissions include:

- view

- add

- change

- delete

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

You are authenticated as \<email>, but are not authorised to access this page.

```

---

# User Visibility and Security Filtering

Admin user selection is automatically filtered to:

- active users only

- unlocked users only

- staff-aware visibility restrictions

This prevents inactive or locked accounts from being assigned within sensitive workflows.

---

# Permission-Based Admin Visibility

Once a user has been assigned:

- a role (group permissions)

- `is_staff=True`

they can successfully login and access the Django admin interface.

However, users will only see:

- models

- admin pages

- actions

- workflows

that their assigned permissions allow them to access.

This means the admin interface dynamically changes depending on the user's assigned role and permissions.

Example:

\| Role    | Example Admin Visibility                     |

\| ------- | -------------------------------------------- |

\| Teller  | Accounts and transaction-related models only |

\| Support | Customer support related models only         |

\| Admin   | Full administrative access                   |

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

- predictable allocation boundaries

- collision prevention

- deterministic identifier issuance

- easier auditing and traceability

- efficient concurrency handling

- allocation integrity across banks

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

- uniqueness

- traceability

- allocation safety

- deterministic provisioning

Example of avoided approach:

```python

random.randint(0, 9999999)

```

Random generation introduces risks such as:

- collision handling complexity

- retry logic during concurrency

- fragmented identifier spaces

- reduced auditability

- non-deterministic allocation behaviour

Sequential allocation provides a safer and more predictable approach.

---

# Concurrency Safety

Identifier generation is protected using:

- database transactions

- row-level locking (`select_for_update`)

This prevents race conditions during concurrent account creation.

Guarantees include:

- no duplicate identifiers

- consistent allocation state

- atomic account creation workflows

---

# Allocation Architecture

The allocation system is composed of several domain components:

\| Component                 | Responsibility                     |

\| ------------------------- | ---------------------------------- |

\| `SortCodeAllocationState` | Tracks global allocation progress  |

\| `SortCodeRangePool`       | Stores reusable allocation ranges  |

\| `SortCode`                | Tracks per-bank issued identifiers |

\| `BankProvisioningService` | Creates and provisions banks       |

\| `AccountService`          | Safely provisions bank accounts    |

This architecture helps maintain strict allocation integrity while supporting scalability and concurrency safety.
