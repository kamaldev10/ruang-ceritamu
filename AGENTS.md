# Agent Instructions - CeritaKita

## Architecture & Entrypoints
- **Framework:** Flask (v3.0) + MySQL (via SQLAlchemy & PyMySQL).
- **Entrypoint:** `run.py` for development (port 5000), `wsgi.py` for production.
- **Database:** MySQL. Automatic creation and table generation on startup via `db.py` and `run.py`.
- **Structure:**
  - `app/`: Core logic, models, routes, and templates.
  - `db.py`: Database connection logic and existence check.
  - `config.py`: Environment-based configurations (development, production, testing).
  - `seed.py`: Script to populate initial data (admin, psychologists, users, posts).

## Development Commands
- **Run App:** `python run.py` (ensure MySQL is running on port 3306).
- **Seed Data:** `python seed.py` (initializes database and default credentials).
- **Shell:** `python -m flask shell` or use context defined in `run.py`.
- **Environment:** Use `.env` for `SECRET_KEY` and database credentials.

## Critical Context
- **Database Setup:** Uses Laragon/MySQL defaults (root, no password) unless overridden in `.env`.
- **Crisis Detection:** Logic in `app/utils.py` monitors for 30+ keywords and triggers admin notifications.
- **Authentication:** Combined login/register routes in `app/routes/auth.py`.
- **Testing:** No specialized test suite found in root. Use `TestingConfig` in `config.py` for manual test scripts.
- **Production:** Uses `waitress` (Windows) or `gunicorn` (Linux).

## Conventions
- **Styling:** Tailwind CSS is likely used (verify in templates).
- **Audit Logs:** All major actions should be logged using `AuditLog` model via `app/utils.py`.
- **Notifications:** Bell/badge system integrated into `app/templates/base.html` and managed via `Notification` model.
