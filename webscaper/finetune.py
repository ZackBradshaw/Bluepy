import re
import json
import ijson  # Import ijson for incremental JSON parsing
from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY", "")
base_url = "http://0.0.0.0:23333"

def timestamped_print(*args):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}", *args)

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

def generate_prompt(title, code, retries=3, timeout=10):
    timestamped_print(f"Generating prompt for title: {title[:30]}...")
    messages = [
        {
            "role": "system",
            "content": f"Generate a prompt for the following Unreal Engine raw blueprint code:"
        },
        {
            "role": "user",
            "content": code
        }
    ]

    for attempt in range(retries):
        try:
            completion = client.chat.completions.create(
                model="deployment-name",  # Replace with your actual deployment name
                messages=messages
            )
            prompt = completion.choices[0].message['content'].strip()  # Access the prompt text
            timestamped_print(f"Generated prompt: {prompt[:30]}...")
            return prompt
        except Exception as e:
            timestamped_print(f"Request failed due to an exception: {e}. Attempt {attempt + 1} of {retries}.")
            time.sleep(timeout)


def process_file(input_file, output_file):
    object_count = 0
    successful_count = 0  # Track the number of successful prompt generations
    processed_prompts = []  # Initialize an empty list to store processed prompts

    with open(input_file, 'r') as f:
        objects = json.load(f)  # Load the entire JSON array into memory
        for obj in objects:
            object_count += 1
            timestamped_print(f"Processing JSON object #{object_count}...")
            if 'code' in obj:
                code = obj['code']  # Use the code directly without preprocessing
                # Generate a title for the code (e.g., based on a pattern or a static string)
                title = f"Blueprint {object_count}"  # Example title generation
                prompt = generate_prompt(title, code)
                if prompt != "Error generating prompt after multiple attempts.":
                    processed_prompt = {"title": title, "code": code, "prompt": prompt}
                    processed_prompts.append(processed_prompt)  # Append to the list of processed prompts
                    successful_count += 1
                    timestamped_print(f"Processed and saved JSON object #{object_count}.")
                else:
                    timestamped_print(f"Failed to generate prompt for JSON object #{object_count}.")
            else:
                timestamped_print(f"Missing 'code' key in JSON object #{object_count}.")

    # Write the list of processed prompts as a JSON array to the output file
    with open(output_file, 'w') as out_f:
        json.dump(processed_prompts, out_f, indent=2)

    timestamped_print(f"Finished processing. Total objects processed: {object_count}, successfully processed: {successful_count}.")

# Adjust the file paths as necessary
input_file_path = './blueprints/processed_blueprints.json'
output_file_path = './blueprints/finetuned_data.json'
# Call the process_file function
process_file(input_file_path, output_file_path)
