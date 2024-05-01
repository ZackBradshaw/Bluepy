import json
import ijson  # Import ijson for incremental JSON parsing
import requests
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

base_url = f"http://localhost:8080"

def timestamped_print(*args):
    """Prints messages with a timestamp."""
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}", *args)

def generate_prompt(instruction, output, retries=3, timeout=10):
    """Generates a prompt using the model hosted in the Docker container."""
    timestamped_print(f"Generating prompt for instruction: {instruction[:30]}...")
    headers = {'Content-Type': 'application/json'}
    data = {
        "inputs": f"Given the Unreal Engine raw blueprint code and its title below, generate a prompt that a user might use to create this blueprint code:\n\nTitle: {instruction}\nBlueprint Code:\n{output}",
        "parameters": {"max_new_tokens": 150}
    }
    
    for attempt in range(retries):
        try:
            timestamped_print(f"Request URL: {base_url}")
            timestamped_print(f"Request Payload: {data}")
            response = requests.post(base_url, headers=headers, json=data, timeout=timeout)
            if response.status_code == 200:
                if response.headers.get('Content-Type') == 'application/json':
                    response_json = response.json()
                    prompt = response_json.get('choices', [{}])[0].get('text', '').strip()
                    timestamped_print(f"Generated prompt: {prompt[:30]}...")
                    return prompt
                else:
                    timestamped_print("Response not in JSON format.")
            else:
                timestamped_print(f"Request failed with status code: {response.status_code}. Attempt {attempt + 1} of {retries}.")
        except requests.exceptions.Timeout:
            timestamped_print(f"Request timed out. Attempt {attempt + 1} of {retries}.")
        except requests.exceptions.RequestException as e:
            timestamped_print(f"Request failed due to an exception: {e}. Attempt {attempt + 1} of {retries}.")
        time.sleep(1)  # Wait for 1 second before retrying to avoid hammering the server

    return "Error generating prompt after multiple attempts."

def process_file(input_file, output_file):
    """Processes each JSON object in the input file and generates prompts."""
    object_count = 0
    with open(input_file, 'rb') as f, open(output_file, 'w') as out_f:
        objects = ijson.items(f, 'item')
        for obj in objects:
            object_count += 1
            timestamped_print(f"Processing JSON object #{object_count}...")
            if 'instruction' in obj and 'output' in obj:
                instruction = obj['instruction']
                output = obj['output']
                prompt = generate_prompt(instruction, output)
                processed_item = {"instruction": prompt}
                json.dump(processed_item, out_f)
                out_f.write("\n")
                timestamped_print(f"Processed and saved JSON object #{object_count}.")
            else:
                timestamped_print(f"Missing 'instruction' or 'output' key in JSON object #{object_count}.")
    timestamped_print(f"Finished processing. Total objects processed: {object_count}.")

# Adjust the file paths as necessary
input_file_path = './blueprints/processed_blueprints.json'
output_file_path = './blueprints/finetuned_data.json'
# Call the process_file function
process_file(input_file_path, output_file_path)