import json
import requests
from dotenv import load_dotenv
import os
import time  # Import time module to use for timestamps
# Load environment variables
load_dotenv()

# Retrieve the POD ID from the environment variables
pod_id = os.getenv("POD_ID")
if not pod_id:
    raise ValueError("POD_ID is not set in the environment variables.")

# Construct the base URL using the POD ID
base_url = f"https://{pod_id}-8080.proxy.runpod.net/generate"

def timestamped_print(*args):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}", *args)

def generate_prompt(instruction, output):
    """
    Constructs a custom request to the specified base URL with the instruction and output.
    """
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Generating prompt for instruction: {instruction[:30]}...")  # Debug print with timestamp
    headers = {'Content-Type': 'application/json'}
    data = {
        "inputs": f"Given the Unreal Engine raw blueprint code and its title below, generate a prompt that a user might use to create this blueprint code:\n\nTitle: {instruction}\nBlueprint Code:\n{output}",
        "parameters": {"max_new_tokens": 150}
    }
    response = requests.post(base_url, headers=headers, json=data)
    response_json = response.json()
    prompt = response_json.get('choices', [{}])[0].get('text', '').strip()
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Generated prompt: {prompt[:30]}...")  # Debug print with timestamp
    return prompt

def process_file(input_file, output_file):
    line_count = 0
    object_count = 0
    with open(input_file, 'r') as f, open(output_file, 'w') as out_f:
        json_str = ""
        for line in f:
            line_count += 1
            json_str += line
            try:
                timestamped_print(f"Attempting to decode JSON object from accumulated lines...")
                data = json.loads(json_str)
                json_str = ""  # Reset json_str after successfully loading a JSON object
                object_count += 1
                timestamped_print(f"Successfully decoded JSON object #{object_count}.")
                
                if 'instruction' in data and 'output' in data:
                    instruction = data['instruction']
                    output = data['output']
                    timestamped_print(f"Generating prompt for JSON object #{object_count}...")
                    prompt = generate_prompt(instruction, output)
                    processed_item = {"instruction": prompt}
                    json.dump(processed_item, out_f)
                    out_f.write("\n")
                    timestamped_print(f"Processed and saved JSON object #{object_count}.")
                else:
                    timestamped_print(f"Missing 'instruction' or 'output' key in JSON object #{object_count}.")
            except json.JSONDecodeError:
                continue  # If JSON is incomplete, continue accumulating lines
        timestamped_print(f"Finished processing. Total lines processed: {line_count}. Total objects processed: {object_count}.")

# Adjust the file paths as necessary
input_file_path = './blueprints/alpaca_lora.json'
output_file_path = './blueprints/finetuned_data.json'
# Call the process_file function
process_file(input_file_path, output_file_path)
