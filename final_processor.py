import base64
import os
import re
from datetime import datetime

import anthropic
from PIL import Image
from pillow_heif import register_heif_opener

import database

register_heif_opener()

UNMATCHED_PATTERN = re.compile(r"^UNMATCHED\s*\((.+)\)$", re.IGNORECASE)


def get_anthropic_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set.")
    return anthropic.Anthropic(api_key=api_key)


def convert_image(image_path):
    if image_path.endswith(".heic") or image_path.endswith(".HEIC"):
        img = Image.open(image_path)
        new_path = image_path.replace(".heic", ".jpg").replace(".HEIC", ".jpg")
        img.save(new_path, "JPEG")
        os.remove(image_path)
        return new_path
    return image_path


def read_image(image_path):
    image_path = convert_image(image_path)
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    return image_data, image_path


def parse_truck(value):
    """Convert truck label to a whole number."""
    return int(float(value.strip()))


def parse_hours(value):
    """Convert hours text to a number, allowing decimals like 8.5."""
    return float(value.strip())


def get_job_list_for_prompt() -> str:
    jobs = database.get_all_jobs()
    if not jobs:
        return "(No official jobs in database yet.)"
    return "\n".join(jobs)


def _parse_job_line(line: str) -> dict:
    parts = line.replace("JOB: ", "").split(" | ")
    if len(parts) < 3:
        raise ValueError(f"Could not parse job line (expected 3 parts): {line}")

    job = parts[0].strip()
    truck = parts[1].replace("TRUCK: ", "").strip()
    hours = parts[2].replace("HOURS: ", "").strip()

    is_unmatched = job.upper().startswith("UNMATCHED")
    original_text = None
    if is_unmatched:
        match = UNMATCHED_PATTERN.match(job)
        if match:
            original_text = match.group(1).strip()
        else:
            original_text = job.replace("UNMATCHED", "").strip(" :()")

    return {
        "job": job,
        "truck": parse_truck(truck),
        "hours": parse_hours(hours),
        "is_unmatched": is_unmatched,
        "original_text": original_text,
    }


def parse_claude_response(claude_response: str) -> dict:
    lines = claude_response.split("\n")
    employee = ""
    timesheet_date = ""
    entries = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("EMPLOYEE:"):
            employee = line.replace("EMPLOYEE: ", "").strip()
        elif line.startswith("DATE:"):
            timesheet_date = line.replace("DATE: ", "").strip()
        elif line.startswith("JOB:"):
            entries.append(_parse_job_line(line))

    if not entries:
        raise ValueError("No job rows found in Claude's response. Check the image or try again.")

    return {
        "employee": employee,
        "timesheet_date": timesheet_date,
        "entries": entries,
    }


def build_claude_prompt() -> str:
    job_list = get_job_list_for_prompt()
    return f"""You are a helpful assistant for a landscaping business.

Here is the official job list:
{job_list}

Extract the timesheet data from the image and return it in this exact format:
EMPLOYEE: [name]
DATE: [date in MM/DD/YYYY format]
JOB: [official job name] | TRUCK: [truck number only, just the number] | HOURS: [hours as a number, use decimals when needed e.g. 8.0 or 8.5]

Rules for job matching:
- Use an official job name from the list ONLY when you are confident the employee's handwriting clearly matches it.
- A confident match means the official job name is clearly identifiable from what was written.
- Never guess or force a match if you are uncertain.
- If you are NOT confident, use this exact format for the job part:
  JOB: UNMATCHED (whatever the employee originally wrote) | TRUCK: [truck number] | HOURS: [hours]
"""


def process_timesheet(image_path: str) -> str:
    image_data, image_path = read_image(image_path)
    image_base64 = base64.b64encode(image_data).decode("utf-8")
    client = get_anthropic_client()

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base64,
                        },
                    },
                    {"type": "text", "text": build_claude_prompt()},
                ],
            }
        ],
    )
    return message.content[0].text


def parsed_data_to_rows(parsed_data: dict) -> list[dict]:
    for entry in parsed_data["entries"]:
        if entry.get("is_unmatched"):
            raise ValueError("Cannot save timesheet with unmatched job entries.")

    submitted = datetime.now().strftime("%m/%d/%Y %I:%M %p")
    rows = []
    for entry in parsed_data["entries"]:
        rows.append(
            {
                "employee": parsed_data["employee"],
                "timesheet_date": parsed_data["timesheet_date"],
                "job_site": entry["job"],
                "truck": entry["truck"],
                "hours": entry["hours"],
                "date_submitted": submitted,
            }
        )
    return rows


def save_timesheet_entries(parsed_data: dict) -> int:
    rows = parsed_data_to_rows(parsed_data)
    return database.insert_timesheet_rows(rows)


def format_parsed_data_for_display(parsed_data: dict) -> str:
    lines = [
        f"EMPLOYEE: {parsed_data['employee']}",
        f"DATE: {parsed_data['timesheet_date']}",
    ]
    for entry in parsed_data["entries"]:
        lines.append(
            f"JOB: {entry['job']} | TRUCK: {entry['truck']} | HOURS: {entry['hours']}"
        )
    return "\n".join(lines)
