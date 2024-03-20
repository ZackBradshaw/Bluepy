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
    This function constructs a custom request to the specified base URL with the instruction and output,
    instructing the model to analyze the Unreal Engine raw blueprint code and come up with a prompt.
    """
    headers = {
        'Content-Type': 'application/json'
    }
    
    data = {
        "inputs": f"Given the Unreal Engine raw blueprint code and its title below, generate a prompt that a user might use to create this blueprint code:\n\nTitle: {instruction}\nBlueprint Code:\n{output}",
        "parameters": {"max_new_tokens": 150}
    }
    
    response = requests.post(base_url, headers=headers, json=data)
    response_json = response.json()
    return response_json.get('choices', [{}])[0].get('text', '').strip()

def process_file(input_file, output_file):
    """
    This function reads the input JSON file, generates prompts for each entry using the custom base URL,
    and saves the results in the output JSON file.
    """
    with open(input_file, 'r') as f:
        data = json.load(f)

    finetuned_data = []

    for entry in data:
        instruction = entry['instruction']
        output = entry['output']
        prompt = generate_prompt(instruction, output)
        finetuned_data.append({
            "instruction": instruction,
            "output": output,
            "generated_prompt": prompt
        })

    with open(output_file, 'w') as f:
        json.dump(finetuned_data, f, indent=4)

# Adjust the file paths as necessary
input_file_path = 'webscaper/blueprints/processed_blueprints.json'
output_file_path = 'webscaper/blueprints/finetuned_data.json'

# Call the process_file function
process_file(input_file_path, output_file_path)
