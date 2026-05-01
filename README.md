Spreadsheet Processor Plan:

Description of program:

we are creating a system that allows a secretary to upload an image of a handwritten timesheet, and using claude api the code extracts the information from the image and formats it into usable data, and then claude (maybe not i cant remember if the code does this on its own or if claude does this part) uses the data to update the spreadsheet and then saves the spreadsheet.

this is going to replace the secretary having to take time out of her day to read each line of the timesheet line by line and type it into the spreadsheet one cell at a time, and this is going to save her a lot of time..

I haven't mentioned this part to you yet but i would like for us to create a new folder for timesheet uploads where the code can automatically detect a file upload and instantly initiate the process. 

plan:

First (we already did this) we need to import our libraries

next I will need to create a new folder (with your instruction on naming conventions etc..)

next create the code that detects when a file (image file) is uploaded

(if possible) make sure that the code stops and sends an error response if the uploaded file isn't an image so that it doesn't mess anything up because it must've been an accident.

next the code needs to determine if the image file is an heic or a jpg file.

next we need to convert our heic image file to jpg if it was an heic

we need to make sure the image is formatted so that claude can read it

then we need to send it to claude (this is a multistep process)

we first need to make sure that claude has access to our official job list so he can cross reference what the employee wrote and the official job name, just so our records can be very clear
then we need to let claude use the official name to replace what they wrote, and then format the data in a usable way.
then we need to use the data to update the spreadsheet 

and then we need to save it.

then print a message that says spreadsheet updated.
