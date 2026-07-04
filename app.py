import io
import os

import streamlit as st

import database
from final_processor import (
    format_parsed_data_for_display,
    parse_claude_response,
    process_timesheet,
    save_timesheet_entries,
)


def configure_secrets() -> None:
    if "ANTHROPIC_API_KEY" in st.secrets and not os.environ.get("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
    if "SUPABASE_URL" in st.secrets and not os.environ.get("SUPABASE_URL"):
        os.environ["SUPABASE_URL"] = st.secrets["SUPABASE_URL"]
    if "SUPABASE_KEY" in st.secrets and not os.environ.get("SUPABASE_KEY"):
        os.environ["SUPABASE_KEY"] = st.secrets["SUPABASE_KEY"]


def clear_upload_session_state() -> None:
    for key in (
        "pending_parsed",
        "claude_raw_result",
        "last_upload_name",
    ):
        if key in st.session_state:
            del st.session_state[key]


def render_upload_tab() -> None:
    st.subheader("Upload Timesheet")
    st.write(
        "Upload a timesheet photo. Data is saved to the database after all job names are matched."
    )

    uploaded_file = st.file_uploader(
        "Choose a timesheet image",
        type=["jpg", "jpeg", "heic", "HEIC"],
        key="timesheet_uploader",
    )

    if uploaded_file is not None:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in (".jpg", ".jpeg", ".heic"):
            st.error("Please upload a JPG or HEIC image.")
            return

        if st.session_state.get("last_upload_name") != uploaded_file.name:
            temp_path = f"temp_upload{ext}"
            jpg_path = "temp_upload.jpg"

            try:
                with st.spinner("Processing your timesheet..."):
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    claude_result = process_timesheet(temp_path)
                    parsed_data = parse_claude_response(claude_result)

                st.session_state.pending_parsed = parsed_data
                st.session_state.claude_raw_result = claude_result
                st.session_state.last_upload_name = uploaded_file.name

                if not any(entry["is_unmatched"] for entry in parsed_data["entries"]):
                    rows_added = save_timesheet_entries(parsed_data)
                    st.success(
                        f"Saved to database successfully! Added {rows_added} row(s)."
                    )
                    with st.expander("Extracted data from timesheet"):
                        st.text(format_parsed_data_for_display(parsed_data))
                    clear_upload_session_state()
            except ValueError as e:
                st.error(f"Could not read the timesheet data: {e}")
                clear_upload_session_state()
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                clear_upload_session_state()
            finally:
                for path in (temp_path, jpg_path):
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                    except OSError:
                        pass

    if "pending_parsed" not in st.session_state:
        return

    parsed_data = st.session_state.pending_parsed
    unmatched_entries = [
        (index, entry)
        for index, entry in enumerate(parsed_data["entries"])
        if entry["is_unmatched"]
    ]

    if unmatched_entries:
        st.warning(
            "Some job names could not be matched automatically. "
            "Resolve each one below before saving."
        )

        official_jobs = database.get_all_jobs()
        if not official_jobs:
            st.info("No official jobs exist yet. Add one below or use the Manage Jobs tab.")

        for index, entry in unmatched_entries:
            st.markdown(f"**Unmatched entry {index + 1}**")
            original_text = entry.get("original_text") or entry["job"]
            st.write(f"Employee wrote: **{original_text}**")

            selected_job = st.selectbox(
                "Select official job",
                options=official_jobs if official_jobs else ["(No jobs yet)"],
                key=f"unmatched_select_{index}",
                disabled=not official_jobs,
            )

            new_job_name = st.text_input(
                "Or type a new official job name",
                key=f"unmatched_new_job_{index}",
            )

            col_add, col_save = st.columns(2)
            with col_add:
                if st.button("Add as New Official Job", key=f"add_job_{index}"):
                    if not new_job_name.strip():
                        st.error("Enter a job name before adding.")
                    else:
                        try:
                            database.add_job(new_job_name)
                            st.success(f"Added '{new_job_name.strip()}' to official jobs.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not add job: {e}")

            with col_save:
                if st.button("Save with Selected Job", key=f"resolve_{index}"):
                    if not official_jobs:
                        st.error("Add an official job first.")
                    else:
                        parsed_data["entries"][index]["job"] = selected_job
                        parsed_data["entries"][index]["is_unmatched"] = False
                        parsed_data["entries"][index]["original_text"] = None
                        st.session_state.pending_parsed = parsed_data
                        st.rerun()

        if not any(entry["is_unmatched"] for entry in parsed_data["entries"]):
            if st.button("Save All Rows to Database", type="primary"):
                try:
                    rows_added = save_timesheet_entries(parsed_data)
                    st.success(
                        f"Saved to database successfully! Added {rows_added} row(s)."
                    )
                    with st.expander("Extracted data from timesheet"):
                        st.text(format_parsed_data_for_display(parsed_data))
                    clear_upload_session_state()
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not save to database: {e}")
        return

    st.info("All job names matched. Review the data below, then save when ready.")
    with st.expander("Extracted data from timesheet"):
        st.text(format_parsed_data_for_display(parsed_data))

    if st.button("Save All Rows to Database", type="primary"):
        try:
            rows_added = save_timesheet_entries(parsed_data)
            st.success(f"Saved to database successfully! Added {rows_added} row(s).")
            with st.expander("Extracted data from timesheet"):
                st.text(format_parsed_data_for_display(parsed_data))
            clear_upload_session_state()
            st.rerun()
        except Exception as e:
            st.error(f"Could not save to database: {e}")


def render_view_edit_tab() -> None:
    st.subheader("View & Edit Data")

    df = database.get_all_timesheets()
    total_records = database.get_timesheet_count()
    st.metric("Total records", total_records)

    if df.empty:
        st.info("No timesheet records yet. Upload a timesheet on the Upload tab.")
        return

    edited_df = st.data_editor(
        df,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "id": None,
            "date_submitted": st.column_config.TextColumn(
                "Date Submitted", disabled=True
            ),
        },
        key="timesheet_data_editor",
    )

    if st.button("Save Changes"):
        try:
            updates = 0
            for _, row in edited_df.iterrows():
                row_id = int(row["id"])
                original_row = df.loc[df["id"] == row_id].iloc[0]
                fields = {
                    "employee": row["employee"],
                    "timesheet_date": row["timesheet_date"],
                    "job_site": row["job_site"],
                    "truck": int(row["truck"]),
                    "hours": float(row["hours"]),
                }
                original_fields = {
                    "employee": original_row["employee"],
                    "timesheet_date": original_row["timesheet_date"],
                    "job_site": original_row["job_site"],
                    "truck": int(original_row["truck"]),
                    "hours": float(original_row["hours"]),
                }
                if fields != original_fields:
                    database.update_timesheet_row(row_id, fields)
                    updates += 1

            st.success(f"Saved {updates} updated row(s).")
            st.rerun()
        except Exception as e:
            st.error(f"Could not save changes: {e}")

    export_df = database.get_timesheets_for_export()
    buffer = io.BytesIO()
    export_df.to_excel(buffer, index=False, engine="openpyxl")
    st.download_button(
        label="Download as Excel",
        data=buffer.getvalue(),
        file_name="timesheets_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render_manage_jobs_tab() -> None:
    st.subheader("Manage Jobs")

    search_text = st.text_input("Search jobs", placeholder="Type to filter job names...")
    new_job_name = st.text_input("New official job name")

    if st.button("Add Job"):
        if not new_job_name.strip():
            st.error("Enter a job name before adding.")
        else:
            try:
                database.add_job(new_job_name)
                st.success(f"Added '{new_job_name.strip()}'.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not add job: {e}")

    jobs = database.get_all_jobs_with_ids()
    if search_text.strip():
        lowered = search_text.strip().lower()
        jobs = [job for job in jobs if lowered in job["job_name"].lower()]

    if not jobs:
        st.info("No jobs found.")
        return

    for job in jobs:
        st.markdown("---")
        col_name, col_edit, col_delete = st.columns([3, 1, 1])
        with col_name:
            st.write(job["job_name"])

        with col_edit:
            if st.button("Edit", key=f"edit_job_{job['id']}"):
                st.session_state[f"editing_job_{job['id']}"] = True

        with col_delete:
            if st.button("Delete", key=f"delete_job_{job['id']}"):
                st.session_state[f"confirm_delete_job_{job['id']}"] = True

        if st.session_state.get(f"editing_job_{job['id']}"):
            updated_name = st.text_input(
                "Updated job name",
                value=job["job_name"],
                key=f"edit_job_name_{job['id']}",
            )
            if st.button("Save Job Name", key=f"save_job_{job['id']}"):
                try:
                    database.update_job(job["id"], updated_name)
                    del st.session_state[f"editing_job_{job['id']}"]
                    st.success("Job updated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not update job: {e}")

        if st.session_state.get(f"confirm_delete_job_{job['id']}"):
            st.warning(f"Delete '{job['job_name']}'? Existing timesheets keep this text.")
            confirm_col, cancel_col = st.columns(2)
            with confirm_col:
                if st.button("Confirm Delete", key=f"confirm_delete_yes_{job['id']}"):
                    try:
                        database.delete_job(job["id"])
                        del st.session_state[f"confirm_delete_job_{job['id']}"]
                        st.success("Job deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not delete job: {e}")
            with cancel_col:
                if st.button("Cancel", key=f"confirm_delete_no_{job['id']}"):
                    del st.session_state[f"confirm_delete_job_{job['id']}"]
                    st.rerun()


def main() -> None:
    st.set_page_config(page_title="Timesheet Processor", layout="wide")
    configure_secrets()

    try:
        database.init_db()
    except Exception as e:
        st.error(f"Database setup failed: {e}")
        st.stop()

    st.title("Timesheet Processor")

    upload_tab, view_tab, jobs_tab = st.tabs(
        ["Upload Timesheet", "View & Edit Data", "Manage Jobs"]
    )

    with upload_tab:
        render_upload_tab()

    with view_tab:
        render_view_edit_tab()

    with jobs_tab:
        render_manage_jobs_tab()


if __name__ == "__main__":
    main()
