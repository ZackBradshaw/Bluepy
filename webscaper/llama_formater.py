import json

def process_blueprint(input_file, output_file):
    """
    Process the blueprint JSON file, extracting 'title' and 'code' fields from a complex structure.
    This version is designed to handle large files and avoid errors related to extra data.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            processed_data = []
            for line in file:
                try:
                    obj = json.loads(line)
                    def extract_title_code(obj):
                        if isinstance(obj, dict):
                            if "title" in obj and "code" in obj:
                                processed_data.append({
                                    "instruction": obj["title"],
                                    "input": "<Picture Attached>",
                                    "output": obj["code"]
                                })
                            for value in obj.values():
                                extract_title_code(value)
                        elif isinstance(obj, list):
                            for item in obj:
                                extract_title_code(item)
                    extract_title_code(obj)
                except json.JSONDecodeError:
                    print(f"Skipping line due to JSON parsing error: {line}")
        
        formatted_data = format_for_llama(processed_data)
        
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(formatted_data, file, indent=4)
        
        print(f"Processed blueprint saved to {output_file}")
    except Exception as e:
        print(f"Error processing blueprint: {e}")

def format_for_llama(processed_data):
    """
    Format the processed data for Llama insertion.
    """
    formatted_data = []
    for item in processed_data:
        modelanswer = item["output"]
        userprompt = item["instruction"]
        systemprompt = item.get("systemprompt", "")
        
        if systemprompt:
            formatted_item = f"<s>[INST] <<SYS>>\n{systemprompt}\n<</SYS>>\n\n{userprompt}[/INST] {modelanswer}</s>"
        else:
            formatted_item = f"<s>[INST] <<SYS>>\n\n<</SYS>>\n\n{userprompt}[/INST] {modelanswer}</s>"
        
        formatted_data.append(formatted_item)
    
    return formatted_data

if __name__ == "__main__":
    input_path = "./blueprints/processed_blueprints.json"
    output_path = "./blueprints/llama_lora.json"
    process_blueprint(input_path, output_path)