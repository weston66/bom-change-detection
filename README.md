# bom-change-detection

Automated BOM change detection pipeline that diffs your bill of materials against a saved snapshot daily, logs every added, removed, or modified part to an audit table, and fires a Slack alert the moment something changes.

---

## Architecture

```
PostgreSQL DB
  └── bom table
       │
       ▼
   detect.py
  ├── snapshot.py ──── bom_snapshot.json (prior state)
  │      │
  │   set-based diff (ADDED / REMOVED / MODIFIED)
  │      │
  ├── db.py ──────────► bom_audit_log (INSERT)
  └── Slack Webhook ──► formatted change alert

GitHub Actions (cron: daily 8am UTC)
  ├── PostgreSQL service container
  ├── Restore snapshot from Actions cache
  ├── Run detect.py
  └── Save updated snapshot to cache
```

---

## Tech Stack

- Python 3.11
- PostgreSQL - BOM data source and audit log store
- psycopg2 - database driver
- JSON snapshots - lightweight state persistence between runs
- Slack Webhooks - change alerting
- GitHub Actions - scheduling and CI runner
- python-dotenv - environment config

---

## What Problem It Solves

BOMs change quietly. An engineer swaps a part, updates a quantity, adds a component - and unless you're watching the right table or someone tells you, you find out when the wrong thing gets built.

In defense and precision manufacturing, untracked BOM changes are an engineering control failure. This tool treats the BOM as an auditable artifact. It snapshots the current state, diffs it against the last known good state at the part level, writes every delta to an audit log with timestamps and change type, and sends a Slack alert with exactly what changed. Runs daily via GitHub Actions with no infrastructure to manage. The audit log is append-only and queryable - useful for traceability during production reviews or customer audits.

---

## How to Run It Locally

**Prerequisites:** Python 3.11+, PostgreSQL running locally or via Docker

**1. Clone the repo**
```bash
git clone https://github.com/weston66/bom-change-detection.git
cd bom-change-detection
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set up environment variables**

Create a `.env` file in the root:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASS=your_db_password
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
```

**4. Apply the audit log migration**
```bash
psql -U your_db_user -d your_db_name -f audit_log.sql
```

**5. Run detection manually**
```bash
python detect.py
```

On first run, no snapshot exists - the script saves the current BOM as the baseline. On subsequent runs it diffs against that baseline and logs any changes.

---

## GitHub Actions - Automated Daily Run

The workflow at `.github/workflows/bom-check.yml` runs automatically at 8am UTC daily.

To trigger manually: go to the Actions tab, select `BOM Change Detection`, click `Run workflow`.

The snapshot is persisted between runs using GitHub Actions cache. No external storage required.

---

## Audit Log Schema

```sql
bom_audit_log
  - bom_id        TEXT
  - change_type   TEXT   -- ADDED | REMOVED | MODIFIED
  - old_value     TEXT
  - new_value     TEXT
  - detected_at   TIMESTAMP
```

---

## Demo

[Watch the demo on Loom](https://www.loom.com/share/466c525710064a20a1a78c4101f68d4e)
