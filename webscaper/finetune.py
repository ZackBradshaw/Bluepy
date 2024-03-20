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
    headers = {'Content-Type': 'application/json'}
    data = {
        "inputs": f"Given the Unreal Engine raw blueprint code and its title below, generate a prompt that a user might use to create this blueprint code:\n\nTitle: {instruction}\nBlueprint Code:\n{output}",
        "parameters": {"max_new_tokens": 150}
    }
    response = requests.post(base_url, headers=headers, json=data)
    response_json = response.json()
    return response_json.get('choices', [{}])[0].get('text', '').strip()

def process_file(input_file, output_file):
    """
    Handles files with multiple JSON objects, ensuring proper JSON format.
    """
    with open(input_file, 'r') as f:
        content = f.readlines()

    finetuned_data = []
    json_str = ""

    for line in content:
        json_str += line.strip()
        try:
            # Attempt to parse the JSON string
            data = json.loads(json_str)
            # If successful, process the data
            instruction = data['instruction']
            output = data['output']
            prompt = generate_prompt(instruction, output)
            finetuned_data.append({"instruction": prompt})
            json_str = ""  # Reset json_str for the next object
        except json.JSONDecodeError:
            # If JSON is incomplete, continue accumulating lines
            continue

    # Save the processed data
    try:
        with open(output_file, 'w') as f:
            json.dump(finetuned_data, f, indent=4)
    except Exception as e:
        print(f"Error saving processed data: {e}")

# Adjust the file paths as necessary
input_file_path = './blueprints/processed_blueprints.json'
output_file_path = './blueprints/finetuned_data.json'
# Call the process_file function
process_file(input_file_path, output_file_path)
