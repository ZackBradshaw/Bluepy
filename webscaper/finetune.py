
import json
import ijson  # Import ijson for incremental JSON parsing
import openai
from dotenv import load_dotenv
import os
import time

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.base_url = os.getnenv("OPENAI_BASE_URL")

def timestamped_print(*args):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}", *args)

def generate_prompt(instruction, output, retries=3, timeout=10):
    timestamped_print(f"Generating prompt for instruction: {instruction[:30]}...")
    data = {
        "prompt": f"Given the Unreal Engine raw blueprint code and its title below, generate a prompt that a user might use to create this blueprint code:\n\nTitle: {instruction}\nBlueprint Code:\n{output}",
        "max_tokens": 150
    }

    for attempt in range(retries):
        try:
            response = openai.Completion.create(**data)
            prompt = response.choices[0].text.strip()
            timestamped_print(f"Generated prompt: {prompt[:30]}...")
            return prompt
        except openai.error.OpenAIError as e:
            timestamped_print(f"Request failed due to an OpenAI error: {e}. Attempt {attempt + 1} of {retries}.")
        except Exception as e:
            timestamped_print(f"Request failed due to an exception: {e}. Attempt {attempt + 1} of {retries}.")
        time.sleep(1)  # Wait for 1 second before retrying to avoid hammering the server

    return "Error generating prompt after multiple attempts."

def process_file(input_file, output_file):
    object_count = 0
    successful_count = 0  # Track the number of successful prompt generations
    with open(input_file, 'rb') as f, open(output_file, 'w') as out_f:
        objects = ijson.items(f, 'item')
        for obj in objects:
            object_count += 1
            timestamped_print(f"Processing JSON object #{object_count}...")
            if 'instruction' in obj and 'output' in obj:
                instruction = obj['instruction']
                output = obj['output']
                prompt = generate_prompt(instruction, output)
                if prompt != "Error generating prompt after multiple attempts.":
                    processed_item = {"instruction": prompt}
                    json.dump(processed_item, out_f)
                    out_f.write("\n")
                    successful_count += 1  # Increment only on successful prompt generation
                    timestamped_print(f"Processed and saved JSON object #{object_count}.")
                else:
                    timestamped_print(f"Failed to generate prompt for JSON object #{object_count}.")
            else:
                timestamped_print(f"Missing 'instruction' or 'output' key in JSON object #{object_count}.")
    timestamped_print(f"Finished processing. Total objects processed: {object_count}, successfully processed: {successful_count}.")

# Adjust the file paths as necessary
input_file_path = './blueprints/alpaca_lora.json'
output_file_path = './blueprints/finetuned_data.json'
# Call the process_file function
process_file(input_file_path, output_file_path)
