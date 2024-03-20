import json
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Retrieve the POD ID from the environment variables
pod_id = os.getenv("POD_ID")
if not pod_id:
    raise ValueError("POD_ID is not set in the environment variables.")

# Construct the base URL using the POD ID
base_url = f"https://{pod_id}-8080.proxy.runpod.net/generate"

def generate_prompt(instruction, output):
    """
    Constructs a custom request to the specified base URL with the instruction and output.
    """
    print(f"Generating prompt for instruction: {instruction[:30]}...")  # Debug print
    headers = {'Content-Type': 'application/json'}
    data = {
        "inputs": f"Given the Unreal Engine raw blueprint code and its title below, generate a prompt that a user might use to create this blueprint code:\n\nTitle: {instruction}\nBlueprint Code:\n{output}",
        "parameters": {"max_new_tokens": 150}
    }
    response = requests.post(base_url, headers=headers, json=data)
    response_json = response.json()
    prompt = response_json.get('choices', [{}])[0].get('text', '').strip()
    print(f"Generated prompt: {prompt[:30]}...")  # Debug print
    return prompt

def process_file(input_file, output_file):
    """
    Processes the file incrementally, handling large files efficiently and updating one object at a time.
    """
    with open(input_file, 'r') as f, open(output_file, 'w') as out_f:
        json_str = ""
        for line in f:
            json_str += line
            try:
                data = json.loads(json_str)
                # Reset json_str after successfully loading a JSON object
                json_str = ""
                # Process the JSON object
                if 'instruction' in data and 'output' in data:
                    print("Processing JSON object...")  # Debug print
                    instruction = data['instruction']
                    output = data['output']
                    prompt = generate_prompt(instruction, output)
                    processed_item = {"instruction": prompt}
                    json.dump(processed_item, out_f)
                    out_f.write("\n")  # Write each JSON object on a new line
                    print("Processed and saved JSON object.")  # Debug print
                else:
                    print("Missing 'instruction' or 'output' key in JSON object.")
            except json.JSONDecodeError:
                # If JSON is incomplete, continue accumulating lines
                continue

# Adjust the file paths as necessary
input_file_path = './blueprints/alpaca_lora.json'
output_file_path = './blueprints/finetuned_data.json'
# Call the process_file function
process_file(input_file_path, output_file_path)
