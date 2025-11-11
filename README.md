# Solaris Web Platform

## Getting started

```bash
python -m venv .venv
.venv\Scripts\activate  # PowerShell
pip install -r requirements.txt
flask db upgrade  # or flask db init && flask db migrate && flask db upgrade on first run
flask run
```

The default configuration stores data in `solaris.db` (SQLite) and uploads in `static/uploads`. You can override these via environment variables:

```bash
set FLASK_APP=app.py
set SOLARIS_SECRET_KEY=super-secret
set DATABASE_URL=sqlite:///custom.db
```

## Features

- Home landing page with quick estimator, Leaflet-based solar map, and translation-ready layout.
- Authentication (register/login/logout) backed by Flask-Login.
- Dashboard summarising reminders, projects, and quick access to estimators.
- Subsidy estimator replicating the Expo subsidy workflow.
- Reminders CRUD with due date/time, categories, and Flash notifications.
- Solar project logging with file uploads for site photos.
- Profile page with editable details, health metrics, and notes (mirroring Expo health data capture).
- Solar health view powered by Leaflet + SunCalc to visualise sun position and shadows.

## Tech stack

- Flask 3.x / Jinja templates
- SQLAlchemy + Flask-Migrate (SQLite by default)
- Flask-WTF & CSRF protection
- Tailwind via CDN, Leaflet, SunCalc for solar computations
- Structured blueprints to mirror Expo navigation (auth, dashboard, projects, reminders, profile, subsidy)
