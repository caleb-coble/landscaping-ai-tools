import os
import anthropic
import openpyxl
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

with open("job_list.txt", "r") as job_list_file:
    job_list_contents = job_list_file.read()

def convert_image(image_path):
    if image_path.endswith(".heic") or image_path.endswith(".HEIC"):
        img = Image.open(image_path)
        new_path = image_path.replace(".heic", ".jpg").replace(".HEIC", ".jpg")
        img.save(new_path, "JPEG")
        return new_path
    return image_path

def read_image(image_path):
    image_path = convert_image(image_path)
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    return image_data, image_path

def process_timesheet(image_path):
    image_data, image_path = read_image(image_path)
    
    import base64
    image_base64 = base64.b64encode(image_data).decode("utf-8")
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": """You are a helpful assistant for a landscaping business.

Here is the official job list:
""" + job_list_contents + """

Extract the timesheet data from the image and return it in this exact format:
EMPLOYEE: [name]
DATE: [date in MM/DD/YYYY format]
JOB: [official job name] | TRUCK: [truck number only, just the number] | HOURS: [hours]"""
                }
            ]}
        ]
    )
    return message.content[0].text

def update_spreadsheet(claude_response):
    try:
        workbook = openpyxl.load_workbook("timesheets_final.xlsx")
        sheet = workbook.active
    except:
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet["A1"] = "Employee"
        sheet["B1"] = "Date"
        sheet["C1"] = "Job Site"
        sheet["D1"] = "Truck"
        sheet["E1"] = "Hours"

    lines = claude_response.split("\n")
    employee = ""
    date = ""
    row = sheet.max_row + 1

    for line in lines:
        if line.startswith("EMPLOYEE:"):
            employee = line.replace("EMPLOYEE: ", "")
        elif line.startswith("DATE:"):
            date = line.replace("DATE: ", "")
        elif line.startswith("JOB:"):
            parts = line.replace("JOB: ", "").split(" | ")
            job = parts[0]
            truck = parts[1].replace("TRUCK: ", "")
            hours = parts[2].replace("HOURS: ", "")
            sheet["A" + str(row)] = employee
            sheet["B" + str(row)] = date
            sheet["C" + str(row)] = job
            sheet["D" + str(row)] = int(truck)
            sheet["E" + str(row)] = int(hours)
            row = row + 1

    sheet.column_dimensions["A"].width = 20
    sheet.column_dimensions["B"].width = 15
    sheet.column_dimensions["C"].width = 35
    sheet.column_dimensions["D"].width = 10
    sheet.column_dimensions["E"].width = 15

    workbook.save("timesheets_final.xlsx")
    print("Spreadsheet updated!")

image_file = "IMG_4869.heic"
result = process_timesheet(image_file)
update_spreadsheet(result)