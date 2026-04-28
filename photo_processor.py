import anthropic
import os
from PIL import Image
from pillow_heif import register_heif_opener
register_heif_opener()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Convert HEIC to JPG if needed
def convert_image(image_path):
    if image_path.endswith(".heic") or image_path.endswith(".HEIC"):
        img = Image.open(image_path)
        new_path = image_path.replace(".heic", ".jpg").replace(".HEIC", ".jpg")
        img.save(new_path, "JPEG")
        return new_path
    return image_path

# Read and encode the image
def read_image(image_path):
    image_path = convert_image(image_path)
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    return image_data, image_path

# Read the job list
with open("job_list.txt", "r") as job_list_file:
    job_list_contents = job_list_file.read()

    # Send image to Claude
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
DATE: [date]
JOB: [official job name] | TRUCK: [truck] | HOURS: [hours]"""
                }
            ]}
        ]
    )
    return message.content[0].text

# Run the processor
image_file = "IMG_4869.heic"
result = process_timesheet(image_file)
print(result)