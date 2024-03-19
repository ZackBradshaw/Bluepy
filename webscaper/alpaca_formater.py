import json

def process_blueprint(input_file, output_file):
    """
    Process the blueprint JSON file, extracting 'title' and 'code' fields from a complex structure.
    This version is designed to handle large files and avoid errors related to extra data.
    """
    try:
        # Open the file using a context manager to ensure it's properly closed after reading.
        with open(input_file, 'r', encoding='utf-8') as file:
            # Process the file line by line to handle large files and avoid loading everything into memory.
            processed_data = []
            for line in file:
                try:
                    # Attempt to parse each line as JSON.
                    obj = json.loads(line)
                    # Function to recursively extract 'title' and 'code' pairs.
                    def extract_title_code(obj):
                        if isinstance(obj, dict):
                            if "title" in obj and "code" in obj:
                                processed_data.append({
                                    "instruction": obj["title"],
                                    "input": "\n",
                                    "output": obj["code"]
                                })
                            for value in obj.values():
                                extract_title_code(value)
                        elif isinstance(obj, list):
                            for item in obj:
                                extract_title_code(item)
                    # Extract 'title' and 'code' from the current object.
                    extract_title_code(obj)
                except json.JSONDecodeError:
                    # Handle lines that cannot be parsed as JSON.
                    print(f"Skipping line due to JSON parsing error: {line}")
        
        # Save the processed data to the output file.
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(processed_data, file, indent=4)
        
        print(f"Processed blueprint saved to {output_file}")
    except Exception as e:
        print(f"Error processing blueprint: {e}")

if __name__ == "__main__":
    input_path = "./blueprints/processed_blueprints.json"
    output_path = "./blueprints/lora_blueprints.json"
    process_blueprint(input_path, output_path)