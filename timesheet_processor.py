import anthropic
import os
import openpyxl

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Read the timesheet
timesheet_file = open("timesheet.txt", "r")
timesheet_contents = timesheet_file.read()
timesheet_file.close()

# Read the job list
job_list_file = open("job_list.txt", "r")
job_list_contents = job_list_file.read()
job_list_file.close()

# Send to Claude
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": """You are a helpful assistant for a landscaping business. 
        
Here is the official job list:
""" + job_list_contents + """

Here is an employee timesheet:
""" + timesheet_contents + """

Extract the data and return it in this exact format, matching each job site to the closest official job name:
EMPLOYEE: [name]
DATE: [date]
JOB: [official job name] | TRUCK: [truck] | HOURS: [hours]
JOB: [official job name] | TRUCK: [truck] | HOURS: [hours]"""}
    ]
)

print(message.content[0].text)

# Create spreadsheet
workbook = openpyxl.Workbook()
sheet = workbook.active

# Add headers
sheet["A1"] = "Employee"
sheet["B1"] = "Date"
sheet["C1"] = "Job Site"
sheet["D1"] = "Truck"
sheet["E1"] = "Hours"

# Parse Claude's response
lines = message.content[0].text.split("\n")

# Extract data from each line
employee = ""
date = ""
row = 2

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
        sheet["D" + str(row)] = truck
        sheet["E" + str(row)] = int(hours)
        row = row + 1

        # Save the spreadsheet
workbook.save("timesheets_auto.xlsx")
print("Spreadsheet saved!")