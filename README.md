# Libraryan Web - Backend

This is the **Libraryan Web backend project** built with Django.

---

## Requirements

* Python 3.11+
* Django 4.x
* Git
* pip

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/kacemielarebi/libraryan-web.git
cd libraryan-web/backend
```

### 2. Create a virtual environment (optional but recommended)

```bash
python -m venv env
env\Scripts\activate   # On Windows
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run database migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Collect static files

```bash
python manage.py collectstatic --noinput
```

### 6. Create an admin account

```bash
python manage.py create_admin
```

You will be prompted to enter a username, email, and password.

---

## ⚠️ Important Configuration Steps

Before running the server, you need to update some settings in `settings.py`:

### 1. Update `ALLOWED_HOSTS`

1. Open the terminal and run:

```bash
ipconfig
```

2. Copy your **IPv4 Address** (e.g., `192.168.8.101`)
3. In `settings.py`:

```python
ALLOWED_HOSTS = ['192.168.8.101', '127.0.0.1', 'localhost']
```

### 2. Add CORS and CSRF settings

```python
# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://192.168.8.101:8000",
    "http://192.168.1.155:8000"
]

# CSRF
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://192.168.8.101:8000",
    "http://192.168.1.155:8000"
]
```

---

### 7. Run the development server

```bash
python manage.py runserver 192.168.8.101:8000
```

---

## Default Admin Login

You can log in using the following account:

* **Email:** `admin@example.com`
* **Password:** `Admin123!@#`

---

## Access the Admin Panel

```
http://192.168.8.101:8000/admin
```

---

*Optional:* You can enhance this README with **screenshots, API documentation, and React setup instructions** for a more professional look.
