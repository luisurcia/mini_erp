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
  services/       business logic (stock rules, sale creation, pipeline)
  blueprints/     routes + forms, one per module (auth, dashboard,
                  inventory, sales, opportunities)
  templates/      Jinja2 templates (Bootstrap 5)
  static/css/     kombucha-themed styling
  seed.py         demo data
config.py          env-based configuration
wsgi.py             app entrypoint
tests/              pytest unit tests for the service layer
```
