import json

def process_blueprint(input_file, output_file):
    """
    Process the blueprint JSON file, mapping 'title' to 'instruction' and 'code' to 'output'.

    Parameters:
    - input_file: Path to the input JSON file (processed_blueprint.json).
    - output_file: Path to the output JSON file.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Assuming the structure of processed_blueprint.json is a list of dictionaries
        processed_data = []
        for item in data:
            processed_item = {
                "instruction": item.get("title", "No title provided"),
                "input": "<Picture Attached>",  # Assuming a static input for demonstration
                "output": item.get("code", "No code provided")
            }
            processed_data.append(processed_item)
        
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(processed_data, file, indent=4)
        
        print(f"Processed blueprint saved to {output_file}")
    except Exception as e:
        print(f"Error processing blueprint: {e}")

if __name__ == "__main__":
    input_path = "./blueprints/processed_blueprints.json"
    output_path = "./blueprints/lora_blueprints.json"
    process_blueprint(input_path, output_path)

