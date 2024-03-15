import json
import re

def process_blueprint(input_file, output_file):
    """
    Process the blueprint JSON file, extracting 'title' and 'code' fields from a complex structure using regex.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)  # Load the JSON content as a dictionary.
        
        # Define regex patterns for 'title' and 'code'.
        title_pattern = re.compile(r'"title":\s*"([^"]+)"')
        code_pattern = re.compile(r'"code":\s*"([^"]+)"')
        
        # Convert the dictionary back to string to use regex.
        data_str = json.dumps(data)
        
        # Search for 'title' and 'code' using regex.
        title_match = title_pattern.search(data_str)
        code_match = code_pattern.search(data_str)
        
        # Extract 'title' and 'code' from matches, defaulting if not found.
        title = title_match.group(1) if title_match else "No title provided"
        code = code_match.group(1) if code_match else "No code provided"
        
        # Prepare the processed data.
        processed_data = {
            "instruction": title,
            "input": "<Picture Attached>",
            "output": code
        }
        
        # Save the processed data to the output file.
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump([processed_data], file, indent=4)  # Wrap in a list to maintain JSON array structure.
        
        print(f"Processed blueprint saved to {output_file}")
    except Exception as e:
        print(f"Error processing blueprint: {e}")

if __name__ == "__main__":
    input_path = "./blueprints/processed_blueprints.json"
    output_path = "./blueprints/lora_blueprints.json"
    process_blueprint(input_path, output_path)