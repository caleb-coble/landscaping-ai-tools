import os

import pandas as pd
import streamlit as st
from supabase import Client, create_client

JOB_LIST_FILE = "job_list.txt"


@st.cache_resource
def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY must be set in Streamlit secrets or environment."
        )
    return create_client(url, key)


def seed_jobs_from_file() -> int:
    client = get_supabase_client()
    response = client.table("jobs").select("id", count="exact").execute()
    existing_count = response.count if response.count is not None else len(response.data)
    if existing_count > 0:
        return 0

    if not os.path.exists(JOB_LIST_FILE):
        return 0

    with open(JOB_LIST_FILE, "r", encoding="utf-8") as job_file:
        job_names = [line.strip() for line in job_file if line.strip()]

    if not job_names:
        return 0

    client.table("jobs").insert([{"job_name": name} for name in job_names]).execute()
    return len(job_names)


def init_db() -> None:
    seed_jobs_from_file()


def get_all_jobs() -> list[str]:
    client = get_supabase_client()
    response = client.table("jobs").select("job_name").order("job_name").execute()
    return [row["job_name"] for row in response.data]


def get_all_jobs_with_ids() -> list[dict]:
    client = get_supabase_client()
    response = client.table("jobs").select("id, job_name").order("job_name").execute()
    return response.data


def add_job(name: str) -> None:
    job_name = name.strip()
    if not job_name:
        raise ValueError("Job name cannot be empty.")

    client = get_supabase_client()
    client.table("jobs").insert({"job_name": job_name}).execute()


def update_job(job_id: int, new_name: str) -> None:
    job_name = new_name.strip()
    if not job_name:
        raise ValueError("Job name cannot be empty.")

    client = get_supabase_client()
    client.table("jobs").update({"job_name": job_name}).eq("id", job_id).execute()


def delete_job(job_id: int) -> None:
    client = get_supabase_client()
    client.table("jobs").delete().eq("id", job_id).execute()


def get_all_timesheets() -> pd.DataFrame:
    client = get_supabase_client()
    response = client.table("timesheets").select("*").order("id", desc=True).execute()
    if not response.data:
        return pd.DataFrame(
            columns=[
                "id",
                "employee",
                "timesheet_date",
                "job_site",
                "truck",
                "hours",
                "date_submitted",
            ]
        )
    return pd.DataFrame(response.data)


def get_timesheet_count() -> int:
    client = get_supabase_client()
    response = client.table("timesheets").select("id", count="exact").execute()
    return response.count if response.count is not None else len(response.data)


def insert_timesheet_rows(rows: list[dict]) -> int:
    if not rows:
        raise ValueError("No rows to insert.")

    client = get_supabase_client()
    client.table("timesheets").insert(rows).execute()
    return len(rows)


def update_timesheet_row(row_id: int, fields: dict) -> None:
    client = get_supabase_client()
    client.table("timesheets").update(fields).eq("id", row_id).execute()


def get_timesheets_for_export() -> pd.DataFrame:
    df = get_all_timesheets()
    if df.empty:
        return df

    column_order = [
        "id",
        "employee",
        "timesheet_date",
        "job_site",
        "truck",
        "hours",
        "date_submitted",
    ]
    return df[column_order]
