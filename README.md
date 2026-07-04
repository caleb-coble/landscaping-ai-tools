# Landscaping Timesheet Processor

Streamlit app for a landscaping business. Upload handwritten timesheet photos, extract data with Claude, and store records in Supabase.

## Features

- **Upload Timesheet** — Process JPG/HEIC images via Claude vision API
- **UNMATCHED job handling** — Resolve unclear job names before saving
- **View & Edit Data** — Browse and edit records, export to Excel
- **Manage Jobs** — Add, search, edit, and delete official job names

## Setup

### 1. Supabase

Create a Supabase project and run this SQL in the SQL Editor:

```sql
create table jobs (
  id bigint generated always as identity primary key,
  job_name text not null unique
);

create table timesheets (
  id bigint generated always as identity primary key,
  employee text not null,
  timesheet_date text not null,
  job_site text not null,
  truck integer not null,
  hours numeric not null,
  date_submitted text not null
);
```

On first run, the app seeds the `jobs` table from `job_list.txt` if it is empty.

### 2. Secrets

Create `.streamlit/secrets.toml` (do not commit this file):

```toml
ANTHROPIC_API_KEY = "your-key"
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-service-role-key"
```

For Streamlit Cloud, paste the same values in **Settings → Secrets**.

### 3. Install and run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project structure

| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI (3 tabs) |
| `final_processor.py` | Image processing, Claude API, parsing |
| `database.py` | Supabase connection and CRUD |
| `job_list.txt` | One-time seed data for official jobs |

## Deployment

Deploy to [Streamlit Community Cloud](https://share.streamlit.io) from GitHub. Use Supabase for persistent storage — local Excel/files do not persist on Cloud.
