# Mini ERP — Kombucha Scoby

A small ERP web app built for a kombucha producer (demo customer:
[@kombucha_scoby](https://instagram.com/kombucha_scoby)) to manage inventory,
record real sales, and track incoming requests/opportunities.

Built with Python (Flask, OOP, layered architecture: models →
repositories → services → routes), SQLAlchemy, and Bootstrap 5.

## Modules

- **Inventory** — flavors/products, stock on hand, restocking, low-stock
  alerts, full stock-movement history.
- **Sales** — record real, multi-line sales; stock is automatically
  consumed and validated (can't oversell).
- **Opportunities** — incoming requests/leads (e.g. an Instagram DM asking
  about wholesale pricing) with a stage pipeline
  (new → contacted → quoted → won/lost), and a one-click **Convert to
  Sale**.
- **Users & roles** — self-service password change, plus admin-only user
  management (create/edit/delete). Three roles: **admin** (everything,
  including user management), **editor** (create/update records), and
  **viewer** (read-only). Enforced both in routes (403 on violation) and
  in the UI (write controls hidden for viewers).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then edit .env: SECRET_KEY, ADMIN_PASSWORD, etc.

flask --app wsgi init-db
flask --app wsgi seed-demo   # optional: creates the admin user + demo data
```

To create/reset the admin user without demo data:

```bash
flask --app wsgi create-admin
```

Upgrading a database created before roles existed (e.g. after pulling
this feature)? `init-db` and `seed-demo` both backfill the new `role`
column automatically — just re-run whichever one you use.

## Run

```bash
flask --app wsgi run --debug
# or: python wsgi.py
```

Visit http://127.0.0.1:5000 and log in with the admin credentials from
`.env` (`ADMIN_USERNAME` / `ADMIN_PASSWORD`).

## Tests

```bash
pytest
```

## Project layout

```
app/
  models/        SQLAlchemy models (BaseModel + domain entities)
  repositories/   generic + domain-specific data access
  services/       business logic (stock rules, sale creation, pipeline,
                  user management)
  blueprints/     routes + forms, one per module (auth, dashboard,
                  inventory, sales, opportunities, users)
  permissions.py  role-based route decorators (admin_required, editor_required)
  schema.py       lightweight in-place upgrades for existing SQLite DBs
  templates/      Jinja2 templates (Bootstrap 5)
  static/css/     kombucha-themed styling
  seed.py         demo data
config.py          env-based configuration
wsgi.py             app entrypoint
tests/              pytest unit tests for the service layer
```
