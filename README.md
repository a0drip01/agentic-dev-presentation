# Django Room Timer Web App

## Overview
A simple Django web app to manage users (doctors, nurses, patients), assign them to rooms, and track timers for each room. Timers are visualized in a live dashboard. Initial data can be loaded from a CSV file.

## Quick Start

1. **Clone the repository and enter the project directory:**
   ```sh
   git clone <your-repo-url>
   cd agentic-dev-presentation/webapp
   ```

2. **Set up the Python virtual environment and install dependencies:**
   ```sh
   make install
   ```

3. **Apply database migrations:**
   ```sh
   .venv/bin/python manage.py migrate
   ```

4. **(Optional) Load sample data:**
   ```sh
   .venv/bin/python manage.py import_users_rooms sample_users_rooms.csv
   ```

5. **Create a superuser for admin access:**
   ```sh
   .venv/bin/python manage.py createsuperuser
   ```

6. **Run the development server:**
   ```sh
   make runserver
   # or
   .venv/bin/python manage.py runserver
   ```

7. **Access the app:**
   - Dashboard: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - Admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

## Features
- Live dashboard with rooms, users, and timer progress bars
- Set, reset, or stop timers for each room from the dashboard
- CSV import for initial user/room data
- Django admin for full data management

## Notes
- The default database is SQLite (file: `db.sqlite3`).
- To reset the database, delete `db.sqlite3` and rerun migrations and imports.
- For production, configure a more robust database (e.g., PostgreSQL).

---

For more details, see the `planning/plan.md` file.

Off to the races...

