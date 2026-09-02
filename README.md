# Kombucha ERP

A small ERP web app for a kombucha producer — manage multi-warehouse
inventory and the production flow, record real sales, track supplies,
and see top customers by consumption. Configured per client from the
Company settings screen (app name, colours, currency, tax, warehouses).

Built with Python (Flask, OOP, layered architecture: models →
repositories → services → routes), SQLAlchemy, and Bootstrap 5.

## Modules

- **Inventory** — flavors/products, stock on hand, restocking, low-stock
  alerts, full stock-movement history.
- **Supplies** — production inputs (bottles, labels, caps) with their own
  catalog/price and per-warehouse stock, mirroring Inventory's pattern.
  Not deducted automatically when a sale is recorded.
- **Sales** — record real, multi-line sales; stock is automatically
  consumed and validated (can't oversell).
- **Top customers** — ranks customers by consumption (total spent,
  bottles, number of sales) over a selected year/month or all-time.
- **Users & roles** — self-service password change, plus admin-only user
  management (create/edit/delete). Roles are per-module rather than a
  flat access level: **admin** (every module, plus Users/Company),
  **bodeguero** (Products, Inventory, Supplies), and **venta** (Sales,
  Products, Top customers, Customers). A module a role can't access is
  both hidden from the nav and blocked at the route (403).
- **Company settings** — tax rate/default and interface language for the
  whole install, plus per-field toggles to simplify the New Product form
  (Short Name, Size, SKU can each be turned off — Unit Price always
  stays required). Whichever fields are hidden also disappear from every
  product picker/grid/chart across the app (Inventory, Sales,
  Top customers, Dashboard), not just the form.

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
pip install -r requirements-dev.txt   # adds pytest-cov, ruff on top of requirements.txt
pytest
ruff check .
```

Both run in CI (`.github/workflows/ci.yml`) on every push/PR — see
CI/CD below.

## Deployment

**Production: cPanel shared hosting** (`server120.web-hosting.com`), account
shared with another Flask app on the same domain (`garageerp`, at
`titourcia.com/garageerp` — never touch that app or the main site in
`public_html/` when deploying this one). No `root`/`sudo`/`systemctl` on
this account: the app runs as a **cPanel "Python App"** (CloudLinux Python
Selector, on top of Phusion Passenger), not a VPS with Nginx/Gunicorn.

| | |
|---|---|
| Production URL | https://titourcia.com/kombuchaerp |
| Host / SSH port | `198.54.116.189`, port **21098** (not 22) |
| User | `titoeyzy` |
| App code | `~/kombuchaerp` (git clone of this repo, branch `main`) |
| Virtualenv | `~/virtualenv/kombuchaerp/3.12` (managed by `cloudlinux-selector`, not `python -m venv`) |
| Database | `~/kombuchaerp/instance/mini_erp.db` (SQLite — has real customer data, back it up before any risky change) |
| `SECRET_KEY` / `ADMIN_PASSWORD` | Set via `cloudlinux-selector set --env-vars`, stored in `~/.cl.selector/python-selector.json` (not in `.env` — there is no `.env` file in production) |
| Server-only files (not in git) | `passenger_wsgi.py`, `init_prod_db.py`, `stderr.log`, `tmp/` — already in place on the server, don't need to be recreated |
| Restart the app | `cloudlinux-selector restart --json --interpreter python --user titoeyzy --app-root /home/titoeyzy/kombuchaerp` (not `systemctl`) |

SSH key: a dedicated deploy key already exists locally at
`~/.ssh/garageerp_deploy` (despite the name, it's the general SSH key for
the `titoeyzy` cPanel account — imported under cPanel → *Security → SSH
Access → Manage SSH Keys*, works for both apps on the account). Connect
with:

```bash
ssh -i ~/.ssh/garageerp_deploy -p 21098 titoeyzy@198.54.116.189
```

This is for **manual/human** access only. CI/CD (below) authenticates
with its own separate `kombuchaerp_deploy` key, scoped to this repo —
see CI/CD for that one.

### Deploying a new release

Pushing to `main` triggers `.github/workflows/ci.yml`, which runs lint +
tests and — if they pass — deploys automatically (see **CI/CD** below).
The steps below are what that pipeline runs on the server; keep them
around for a one-off manual deploy (e.g. CI is down, or you're deploying
something that isn't in `main` yet).

```bash
ssh -i ~/.ssh/garageerp_deploy -p 21098 titoeyzy@198.54.116.189
cd ~/kombuchaerp

# 1. Back up the database first (see Backups below) — always, since
#    production has real customer data.
KOMBUCHAERP_APP_DIR=/home/titoeyzy/kombuchaerp \
KOMBUCHAERP_BACKUP_DIR=/home/titoeyzy/backups/kombuchaerp \
  ~/kombuchaerp/deploy/backup_sqlite.sh

# 2. Pull the new code.
git pull origin main

# 3. Install/update dependencies if requirements.txt changed.
cloudlinux-selector install-modules --json --interpreter python \
  --user titoeyzy --app-root /home/titoeyzy/kombuchaerp \
  --requirements-file requirements.txt

# 4. Apply schema changes (safe to always run — init-db only creates
#    missing tables/columns, never touches existing data).
source ~/virtualenv/kombuchaerp/3.12/bin/activate
export FLASK_APP=wsgi.py
flask init-db

# 5. Restart.
cloudlinux-selector restart --json --interpreter python --user titoeyzy \
  --app-root /home/titoeyzy/kombuchaerp

# 6. Verify.
curl -s -o /dev/null -w '%{http_code}\n' https://titourcia.com/kombuchaerp/auth/login
# should print 200; also check for fresh errors:
tail -30 ~/kombuchaerp/stderr.log
```

### CI/CD

`.github/workflows/ci.yml` runs a `test` job on every push/PR (`ruff
check .`, then `pytest`), and a `deploy` job only on push to `main` and
only if `test` passed. `deploy` runs the same steps as the manual
process above over SSH — backup, `git pull --ff-only`, install
dependencies, `flask init-db`, `cloudlinux-selector restart` — and
**fails the pipeline if `GET /health` doesn't respond `200` afterward**,
so a broken deploy never shows green.

`/health` (added for this) checks the app can reach the database
(`SELECT 1`) and returns `{"status": "ok", "database": "ok"}` with a
`200`, or `503` if the DB check fails. No auth required — it's meant to
be curled by CI/uptime checks, not browsed.

**One-time setup, done 2026-08-26** (documented for reference — same
idea as "First-time setup" below, just for CI instead of the app
itself):

1. Generated a deploy key dedicated to this repo, separate from the
   shared `garageerp_deploy` one used for manual access (per #13):
   `ssh-keygen -t ed25519 -f kombuchaerp_deploy -C "kombuchaerp-ci"`.
2. Imported the **public** half into cPanel → *Security → SSH Access →
   Manage SSH Keys → Import Key*, and authorized it.
3. Added the **private** half and connection details as repo secrets
   (`Settings → Secrets and variables → Actions`):

   | Secret | Value |
   |---|---|
   | `SSH_HOST` | `198.54.116.189` |
   | `SSH_USER` | `titoeyzy` |
   | `SSH_PRIVATE_KEY` | Private half of `kombuchaerp_deploy` from step 1 |

4. The `deploy` job targets a GitHub **Environment** named `production`
   (`github.com/luisurcia/mini_erp/settings/environments`) — it was
   auto-created (no protection rules) the first time the workflow
   referenced it; add rules there (e.g. required reviewer before
   deploying) if ever wanted.

Verified end-to-end the same day: pushed #13's commit, `test` passed,
`deploy` connected with the new key, ran the backup/pull/restart
sequence, and the post-restart `/kombuchaerp/health` check passed —
confirmed independently with a direct `curl` against production
afterward too.

### First-time setup (already done — documented for reference)

The steps below were already run once to get the app onto the server.
They shouldn't need repeating unless the app is rebuilt from scratch.

1. SSH key imported into cPanel (see above).
2. Repo cloned: `git clone https://github.com/luisurcia/mini_erp.git ~/kombuchaerp` (public repo, no deploy key needed).
3. Python App created via `cloudlinux-selector create` with `--app-uri kombuchaerp --startup-file wsgi.py --entry-point app` (this also generates `passenger_wsgi.py` and the Passenger block in `~/public_html/kombuchaerp/.htaccess` — don't hand-edit either).
4. Dependencies installed via `cloudlinux-selector install-modules` (see step 3 above).
5. Env vars set via `cloudlinux-selector set --env-vars '{"SECRET_KEY": "...", "ADMIN_PASSWORD": "..."}'` — real values, never the dev defaults from `config.py`.
6. `flask init-db` run once to create the schema.

### Backups

`deploy/backup_sqlite.sh` backs up the database with `sqlite3 .backup`
(safe to run while the app is live) and compresses the result. Configured
in the `titoeyzy` crontab (no `sudo`), daily at 2:00 am, alongside the
existing `garageerp` backup job:

```
0 2 * * * KOMBUCHAERP_APP_DIR=/home/titoeyzy/kombuchaerp KOMBUCHAERP_BACKUP_DIR=/home/titoeyzy/backups/kombuchaerp /home/titoeyzy/kombuchaerp/deploy/backup_sqlite.sh >> /home/titoeyzy/kombuchaerp/logs/backup.log 2>&1
```

Backups land in `~/backups/kombuchaerp/`, retained locally for 30 days
(`KOMBUCHAERP_BACKUP_RETENTION_DAYS`). Not yet done: syncing that
directory to off-server storage (e.g. weekly to S3 or another host) —
out of scope for the script, which only handles the daily local backup.

## Scoby ERP deployment (`client/scoby` branch)

A second, independent production instance for Scoby Kombucha specifically —
same cPanel account/server as above, but its own "Python App", its own
virtualenv, its own SQLite database, and deployed from the `client/scoby`
branch instead of `main`. `main` stays the generic product line; this is
where Scoby's branding/color/multi-warehouse/etc. customizations actually
run live.

| | |
|---|---|
| Production URL | https://titourcia.com/scobyerp |
| Host / SSH port | same as kombuchaerp: `198.54.116.189`, port **21098** |
| User | `titoeyzy` (same account) |
| App code | `~/scobyerp` (git clone of this repo, branch `client/scoby`) |
| Virtualenv | `~/virtualenv/scobyerp/3.12` |
| Database | `~/scobyerp/instance/mini_erp.db` — separate file, not shared with kombuchaerp's |
| `SECRET_KEY` / `ADMIN_PASSWORD` | Own values, set the same way as kombuchaerp (`cloudlinux-selector set --env-vars`) — never reuse kombuchaerp's |
| Restart the app | `cloudlinux-selector restart --json --interpreter python --user titoeyzy --app-root /home/titoeyzy/scobyerp` |

### First-time setup (do this once, manually, over SSH)

Same shape as kombuchaerp's original first-time setup — nothing here is
automated by CI, it only takes over once the app exists and has a schema:

```bash
ssh -i ~/.ssh/garageerp_deploy -p 21098 titoeyzy@198.54.116.189

# 1. Clone the repo on the client/scoby branch.
git clone --branch client/scoby https://github.com/luisurcia/mini_erp.git ~/scobyerp

# 2. Create the Python App (also generates passenger_wsgi.py and the
#    Passenger block in ~/public_html/scobyerp/.htaccess automatically —
#    don't hand-edit either). --version is required: without it this
#    silently defaults to the system's Python (3.6 here), not 3.12.
cloudlinux-selector create --json --interpreter python \
  --user titoeyzy --app-root /home/titoeyzy/scobyerp \
  --app-uri scobyerp --version 3.12 --startup-file wsgi.py --entry-point app

# 2b. `create` overwrites wsgi.py with its own placeholder
#     ("It works!") stub — restore the repo's real one.
cd ~/scobyerp && git checkout -- wsgi.py

# 3. Install dependencies into the new virtualenv.
cloudlinux-selector install-modules --json --interpreter python \
  --user titoeyzy --app-root /home/titoeyzy/scobyerp \
  --requirements-file requirements.txt

# 4. Set real env vars (never the dev defaults from config.py) — generate
#    a fresh SECRET_KEY and ADMIN_PASSWORD, don't reuse kombuchaerp's.
cloudlinux-selector set --json --interpreter python \
  --user titoeyzy --app-root /home/titoeyzy/scobyerp \
  --env-vars '{"SECRET_KEY": "...", "ADMIN_PASSWORD": "..."}'

# 5. `instance/` is gitignored, so the fresh clone doesn't have it —
#    SQLite won't create the missing parent directory for you, it just
#    fails with "unable to open database file".
mkdir -p ~/scobyerp/instance

# 6. Create the schema and seed Scoby's demo data (customers, products,
#    a sale or two) so there's something to look at on first login —
#    swap for `flask init-db` alone later if a clean slate is wanted
#    instead.
source ~/virtualenv/scobyerp/3.12/bin/activate
export FLASK_APP=wsgi.py
flask seed-demo

# 7. Restart and verify.
cloudlinux-selector restart --json --interpreter python \
  --user titoeyzy --app-root /home/titoeyzy/scobyerp
curl -s -o /dev/null -w '%{http_code}\n' https://titourcia.com/scobyerp/health
```

### CI/CD

`.github/workflows/deploy-scoby.yml` mirrors `ci.yml` exactly, but triggers
on `client/scoby` instead of `main`, deploys to `~/scobyerp` instead of
`~/kombuchaerp`, and checks `/scobyerp/health` instead of
`/kombuchaerp/health`. It reuses the same repo-level secrets
(`SSH_HOST`/`SSH_USER`/`SSH_PRIVATE_KEY`) as kombuchaerp's pipeline — same
server and account, so no separate deploy key was generated for this one —
and deploys through its own GitHub **Environment**, `scoby-production`
(separate from kombuchaerp's `production`, so the two apps' deploy history
shows up distinctly under *Deployments*).

Once the first-time setup above has run, pushing to `client/scoby` is
enough to ship a change — same as `main` does for kombuchaerp.

### Backups

Same `deploy/backup_sqlite.sh` script, pointed at scobyerp's own paths via
env vars (the var names are prefixed `KOMBUCHAERP_` in the script itself,
but that's just the script's original naming — it works for any app
directory passed in). Add a second cron line alongside the existing one —
**edit the crontab with `crontab -e`, or write out the full file and load
it with `crontab <file>`; don't pipe a partial `crontab -l` through
`| crontab -`** in one shell command, since a subshell hiccup there can
silently replace the whole crontab with just the new line (this happened
once during setup and had to be restored from the previously-known-good
`crontab -l` output — there's no automatic backup of the crontab itself):

```
0 2 * * * KOMBUCHAERP_APP_DIR=/home/titoeyzy/scobyerp KOMBUCHAERP_DB_PATH=/home/titoeyzy/scobyerp/instance/mini_erp.db KOMBUCHAERP_BACKUP_DIR=/home/titoeyzy/backups/scobyerp /home/titoeyzy/scobyerp/deploy/backup_sqlite.sh >> /home/titoeyzy/scobyerp/logs/backup.log 2>&1
```

## Project layout

```
app/
  models/        SQLAlchemy models (BaseModel + domain entities)
  repositories/   generic + domain-specific data access
  services/       business logic (stock rules, sale creation, pipeline,
                  user management)
  blueprints/     routes + forms, one per module (auth, dashboard,
                  inventory, supplies, sales, top_customers, users)
  permissions.py  role-based route decorators (admin_required, module_required)
  schema.py       lightweight in-place upgrades for existing SQLite DBs
  templates/      Jinja2 templates (Bootstrap 5)
  static/css/     kombucha-themed styling
  seed.py         demo data
config.py          env-based configuration
wsgi.py             app entrypoint
tests/              pytest unit tests for the service layer
```
