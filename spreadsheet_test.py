import openpyxl

workbook = openpyxl.Workbook()
sheet = workbook.active

sheet["A1"] = "Employee Name"
sheet["B1"] = "Job Site"
sheet["C1"] = "Truck"
sheet["D1"] = "Hours Worked"

sheet["A2"] = "John Smith"
sheet["B2"] = "123 Oak Street"
sheet["C2"] = "Truck 4"
sheet["D2"] = 8

workbook.save("timesheets.xlsx")
print("Spreadsheet created!")