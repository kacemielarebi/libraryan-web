# libraryan-web
libraryan-web
# Libraryan Web - Backend

This is the **Libraryan Web** backend project built with Django.

## Requirements

- Python 3.11+
- Django 4.x
- Git
- pip

## Setup Instructions

1. **Clone the repository:**

```bash
git clone https://github.com/kacemielarebi/libraryan-web.git
cd libraryan-web/backend
Install dependencies:
pip install -r requirements.txt
Run database migrations:
python manage.py makemigrations
python manage.py migrate
Collect static files:
python manage.py collectstatic --noinput
Create an admin account:
python manage.py create_admin

You will be prompted to enter a username, email, and password for the admin account.

Run the development server:
python manage.py runserver 192.168.8.101:8000

Access the admin panel at: http://192.168.8.101:8000/admin