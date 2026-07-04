import os

import streamlit as st

from final_processor import process_timesheet, update_spreadsheet

st.title("Timesheet Processor")
st.write("Upload a timesheet photo and it will automatically be added to the spreadsheet.")

uploaded_file = st.file_uploader("Choose a timesheet image", type=["jpg", "jpeg", "heic", "HEIC"])

if uploaded_file is not None:
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in (".jpg", ".jpeg", ".heic"):
        st.error("Please upload a JPG or HEIC image.")
    else:
        temp_path = f"temp_upload{ext}"
        jpg_path = "temp_upload.jpg"

        st.write("Processing your timesheet...")

        try:
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            result = process_timesheet(temp_path)
            rows_added = update_spreadsheet(result)

            st.success(f"Spreadsheet updated successfully! Added {rows_added} row(s).")
            with st.expander("Extracted data from timesheet"):
                st.text(result)
        except ValueError as e:
            st.error(f"Could not read the timesheet data: {e}")
        except Exception as e:
            st.error(f"Something went wrong: {e}")
        finally:
            for path in (temp_path, jpg_path):
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError:
                    pass
