import anthropic
import os
import time

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

file = "job1.txt"
job_report = open(file, "r")
contents = job_report.read()
job_report.close()

for attempt in range(3):
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": "You are a helpful assistant for a landscaping business. Please provide a professional quote for this job request:\n\n" + contents}
            ]
        )
        print(message.content[0].text)
        break
    except Exception as e:
        print("Attempt " + str(attempt + 1) + " failed, retrying...")
        time.sleep(5)

output = open("quote_output.txt", "w", encoding="utf-8")
output.write(message.content[0].text)
output.close()
print("Quote saved to quote_output.txt!")


