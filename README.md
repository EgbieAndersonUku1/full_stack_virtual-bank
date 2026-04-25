

⚠️ This project is actively under development

# Virtual Bank & Wallet (Django + PostgreSQL) Ongoing

This project is a **virtual banking simulation system** built with Django and PostgreSQL.  
It includes wallet functionality, user management, and financial operations in a simulated environment.

---

##Project Setup

### 1. Clone the repository

```bash
git clone https://github.com/EgbieAndersonUku1/full_stack_virtual-bank .

````

---

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**macOS / Linux**

```bash
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🗄️ Database Setup (PostgreSQL + pgAdmin)

### Requirements

Make sure you have installed:

* Python 3.10+
* PostgreSQL
* pgAdmin 4
* pip / virtualenv

---

## Installation

### Install PostgreSQL & pgAdmin

1. Download pgAdmin: [https://www.pgadmin.org/download/](https://www.pgadmin.org/download/)
2. Download PostgreSQL: [https://www.postgresql.org/download/](https://www.postgresql.org/download/)
3. During installation, set a password for the `postgres` user
4. Restart your computer if pgAdmin does not load correctly

---

## Create the Database

### Using pgAdmin:

* Open pgAdmin
* Expand **Servers → PostgreSQL**
* Right-click **Databases**
* Click **Create → Database**
* Set:

  * **Database name:** `virtual_bank` (or your choice)
  * **Owner:** `postgres`
* Click **Save**

---

## 🔐 Environment Variables

Create a `.env` file in the project root using `.env.example`:

```env
DB_NAME=
DB_USER=postgres
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
```

### Fill in:

* `NAME` → your database name
* `USER` → usually `postgres`
* `PASSWORD` → your PostgreSQL password
* `HOST` → keep as `localhost`
* `PORT` → keep as `5432`

⚠️ Never commit `.env` to GitHub

---

## ⚙️ Django Database getenvuration


```bash

```

Then update `settings.py`:

```python


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': getenv('DB_NAME'),
        'USER': getenv('DB_USER'),
        'PASSWORD': getenv('DB_PASSWORD'),
        'HOST': getenv('DB_HOST'),
        'PORT': getenv('DB_PORT'),
    }
}
```

---

## 🧱 Run Migrations

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

## ▶️ Run the Server

```bash
python manage.py runserver
```

Visit:

* App: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)

* Admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🧪 Troubleshooting

### ❌ Connection refused

* Ensure PostgreSQL service is running
* Check pgAdmin server status

### ❌ Authentication failed

* Verify username/password in `.env`
* Check PostgreSQL role settings

### ❌ Database does not exist

* Confirm database name matches pgAdmin

---

## 📌 Notes

* pgAdmin is only a database management GUI
* Django connects directly to PostgreSQL
* Always use environment variables for sensitive data

```
