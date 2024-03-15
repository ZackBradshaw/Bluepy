import pandas as pd
import json
import sys
import os

def process_json_to_csv(json_path, output_csv_path):
    """
    Processes JSON data, focusing on 'title' and 'code' fields, and saves it to a CSV file.
    Maps 'title' to 'question' and 'code' to 'answer'. Uses placeholders for 'ChunkIDs' and 'ChunkTexts'.
    """
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Extract and rename fields, use placeholders for missing data
        processed_data = [
            {
                "ChunkIDs": "N/A",  # Placeholder value
                "ChunkTexts": "N/A",  # Placeholder value
                "Question": item["title"],
                "Answer": item["code"],
                "Quoted_Text_ID": "N/A"  # Placeholder value or generate if possible
            }
            for item in data
        ]
        
        df = pd.DataFrame(processed_data)
        
        df.to_csv(output_csv_path, index=False)
        print(f"Data saved to CSV file {output_csv_path}.")
    except Exception as e:
        print(f"Failed to process JSON and create CSV: {e}")

def main():
    # Adjusted to expect JSON path and output CSV path as arguments
    if len(sys.argv) < 3:
        print("Usage: python tuna.py <path_to_json> <output_csv_path>")
        sys.exit(1)

    json_path = sys.argv[1]
    output_csv_path = sys.argv[2]

    if not os.path.exists(json_path):
        print(f"File {json_path} does not exist!")
        sys.exit(1)

    process_json_to_csv(json_path, output_csv_path)

if __name__ == "__main__":
    main()
