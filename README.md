

## ⚠️ This project is actively under developmen
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
