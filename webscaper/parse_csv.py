import pandas as pd
import json
import logging

# Setup enhanced logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_json_and_create_csv(json_path, output_csv_path):
    """
    Reads JSON data from a file, processes it, and saves it to a CSV file.
    """
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        logging.info(f"JSON file {json_path} successfully read.")
        
        # Assuming the JSON data is a list of dictionaries
        df = pd.DataFrame(data)
        
        # If you need to transform or filter the data, do it here
        
        df.to_csv(output_csv_path, index=False)
        logging.info(f"Data saved to CSV file {output_csv_path}.")
    except Exception as e:
        logging.error(f"Failed to read JSON and create CSV: {e}")

if __name__ == "__main__":
    json_path = "./blueprints/processed_blueprints.json"
    output_csv_path = "./blueprints/structured_blueprints_for_tuna.csv"
    read_json_and_create_csv(json_path, output_csv_path)