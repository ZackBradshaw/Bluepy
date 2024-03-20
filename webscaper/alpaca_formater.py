import json

def process_blueprint(input_file, output_file):
    """
    Process the blueprint JSON file, extracting 'title' and 'code' fields from a complex structure.
    This version is designed to handle large files and avoid errors related to extra data.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            processed_data = []
            json_string = ''
            for line in file:
                json_string += line.strip()
                try:
                    obj = json.loads(json_string)
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
                    json_string = ''  # Reset for the next object
                except json.JSONDecodeError:
                    # If a JSONDecodeError occurs, it might be due to an incomplete JSON object.
                    # The loop continues, appending more lines to json_string.
                    continue

        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(processed_data, file, indent=4)

        print(f"Processed blueprint saved to {output_file}")
    except Exception as e:
        print(f"Error processing blueprint: {e}")

if __name__ == "__main__":
    input_path = "webscaper/blueprints/processed_blueprints.json"
    output_path = "webscaper/blueprints/alpaca_lora.json"
    process_blueprint(input_path, output_path)