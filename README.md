

## ⚠️ This project is actively under development
## Virtual Bank & Wallet (Django + PostgreSQL)

This project is a **virtual banking simulation system** built with Django and PostgreSQL.
It includes wallet functionality, user management, and financial operations in a simulated environment.

---

## Python Version Requirements (IMPORTANT)

This project is tested and recommended with:

* Python **3.11 – 3.13.x**
* Python **3.14+ is not recommended yet** due to partial ecosystem support across Django dependencies and third-party packages

See [https://www.python.org/downloads/](http://127.0.0.1:8000/) to see the stable python

### Recommended check before setup

```bash
python --version
```

---

##  Project Setup

## 1. Clone the repository

```bash
git clone https://github.com/EgbieAndersonUku1/full_stack_virtual-bank .
```

---

## 2. Create a virtual environment (IMPORTANT)

### Recommended (ensures correct Python version)

```bash
py -3.13 -m venv venv
```

If Python 3.13 is not installed, use:

```bash
py -3.12 -m venv venv
```

---

## Activate virtual environment

### Windows (PowerShell)

```bash
.\venv\Scripts\Activate.ps1
```

### Windows (CMD)

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

---

## 3. Upgrade pip (recommended)

```bash
python -m pip install --upgrade pip
```

---

## 4. Install dependencies

```bash
pip install -r requirements.txt
```


---

## 🗄️ Database Setup (PostgreSQL + pgAdmin)

## Requirements

* Python 3.11–3.13
* PostgreSQL
* pgAdmin 4
* pip / virtualenv

---

## Install PostgreSQL & pgAdmin

1. Download pgAdmin: [https://www.pgadmin.org/download/](https://www.pgadmin.org/download/)
2. Download PostgreSQL: [https://www.postgresql.org/download/](https://www.postgresql.org/download/)
3. Set `postgres` password during installation
4. Restart system if pgAdmin does not load

---

## Create Database

In pgAdmin:

* Servers → PostgreSQL
* Right-click **Databases**
* Create → Database
* Name: `virtual_bank`
* Owner: `postgres`

---

##  Environment Variables

Create `.env` file:

```env
NAME=
USER=postgres
PASSWORD=
HOST=localhost
PORT=5432
```

⚠️ Never commit `.env` to GitHub

---

## Django Database Configuration

Then configure `settings.py`:

```

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': getenv("NAME"),
        'USER': getenv('USER'),
        'PASSWORD': getenv("PASSWORD"),
        'HOST': getenv("HOST"),
        'PORT': getenv("PORT"),
    }

}
```

---

## Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 👤 Create Superuser

```bash
python manage.py createsuperuser
```

---

## Open two terminals

### In termainal one run Server

```bash
python manage.py runserver
```


### In terminal two run Django-q 

This allows tasks to be run in the background e.g sending emails

```bash

python manage.py qcluster
```

---

## Some Available Routes

* App: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* Dashboard: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
* Terms: [http://127.0.0.1:8000/terms-and-conditions](http://127.0.0.1:8000/terms-and-conditions)
* Admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

# 🧪 Troubleshooting

## ❌ Dependency or import errors

* Ensure correct Python version (3.11–3.13)
* Recreate virtual environment

## ❌ Database connection failed

* Check PostgreSQL service is running
* Verify `.env` values

## ❌ Migration issues

```bash
python manage.py migrate --run-syncdb
```

---

## 📌 Notes

* Django connects directly to PostgreSQL (pgAdmin is only a GUI)
* Always use environment variables for secrets
* Keep dependencies pinned for production stability
* Recreate venv if Python version changes

---


---



## Create banks and bank accounts


This project uses **sequential allocation** for both sort codes and account numbers.

The system intentionally does **not** use random number generation for financial identifiers.

### Why Sequential Generation Is Used

Sequential generation provides several important guarantees required in banking and financial systems:

- predictable allocation boundaries
- collision prevention
- deterministic identifier issuance
- easier auditing and traceability
- efficient concurrency handling
- allocation integrity across banks


In this app, a superuser can add a limited amount of banks to the virtual bank, and when each bank is created, it is assigned an isolated numeric allocation block. All sort codes and account numbers generated for that bank are issued sequentially within the assigned range.

Example:

```text
Bank A allocation block:
0 → 200000

Generated identifiers:
The bank then creates the following accounts:

Sort Code:     000001
Account No:    00000001

Next:
Sort Code:     000002
Account No:    00000002

Next:
Sort Code:     000003
Account No:    00000003
````

Another bank receives a completely different allocation range:

```text
Bank B allocation block:
200001 → 400000

Generated identifiers:
Sort Code:     200001
Account No:    00000001
```

This design guarantees that identifier spaces never overlap between banks.

---

## Why Random Generation Is Avoided

Random generation was intentionally avoided because financial systems require strong guarantees around uniqueness, traceability, and allocation safety.

The system could have used a random generator as so

```
random.randint(0, 9999999)
```

But Using random identifiers introduces several risks:

* collision handling complexity
* retry logic under concurrency
* fragmented identifier space
* poor auditability
* non-deterministic allocation behaviour
* reduced operational transparency

Sequential allocation provides a safer and more deterministic approach for core banking infrastructure.

---

## Concurrency Safety

Identifier generation is protected using database transactions and row-level locking (`select_for_update`) to prevent race conditions during concurrent account creation.

This ensures that:

* two requests cannot generate the same identifier
* allocation state remains consistent
* account creation remains atomic

---

## Allocation Architecture

The allocation system is composed of several domain components:

| Component                 | Responsibility                                    |
| ------------------------- | ------------------------------------------------- |
| `SortCodeAllocationState` | Tracks global allocation progress                 |
| `SortCodeRangePool`       | Stores reusable allocation ranges                 |
| `SortCode`                | Tracks per-bank issued identifiers                |
| `BankProvisioningService` | Tracks and creates new banks               |

| `AccountService`          | Safely provisions bank accounts                   |

This architecture allows the system to scale safely while maintaining strict allocation integrity and prevents random numbers for account


