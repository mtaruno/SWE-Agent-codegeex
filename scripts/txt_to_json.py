import json 


file = "/Users/matthewtaruno/Library/Mobile Documents/com~apple~CloudDocs/Dev/SWE-agent/example_messages.txt"
import json

# Read the content of the txt file
with open(file, 'r') as file:
    content = file.read()

# Split the content into lines
lines = content.splitlines()

# Initialize a list to hold the JSON objects
json_entries = []

# Process each line to form dictionaries
current_role = None
current_content = []

for line in lines:
    if line.startswith("[{'role':") or line.startswith("{'role':"):
        if current_role and current_content:
            json_entries.append({'role': current_role, 'content': "\n".join(current_content).strip()})
        current_role = line.split("'")[3]
        current_content = [line.split("', 'content': '", 1)[1]]
    else:
        current_content.append(line)

# Append the last entry
if current_role and current_content:
    json_entries.append({'role': current_role, 'content': "\n".join(current_content).strip()})

# Convert the list of JSON objects to a JSON string
json_output = json.dumps(json_entries, indent=4)

# Save the JSON content to a file
with open('output.json', 'w') as json_file:
    json_file.write(json_output)

print("Conversion complete! The JSON content is saved in output.json.")