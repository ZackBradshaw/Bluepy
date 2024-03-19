import json
import pandas as pd
import re
import os
import logging

REDUNDANT_FIELDS = {
    'bIsReference': 'False',
    'bIsConst': 'False',
    'bIsWeakPointer': 'False',
    'bIsUObjectWrapper': 'False',
    'bSerializeAsSinglePrecisionFloat': 'False',
}

# Setup enhanced logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_csv(csv_path):
    """
    Reads a CSV file and returns a DataFrame.
    """
    if not os.path.exists(csv_path):
        logging.error(f"CSV file {csv_path} does not exist.")
        return None
    try:
        df = pd.read_csv(csv_path)
        logging.info(f"CSV file {csv_path} successfully read.")
        return df
    except Exception as e:
        logging.error(f"Failed to read CSV file {csv_path}: {e}")
        return None

def extract_blueprint_elements(blueprint_code):
    """
    Extracts elements and their properties from the raw blueprint code.
    """
    elements = []
    current_element = {}
    for line in blueprint_code.split('\n'):
        if "Begin Object" in line or "End Object" in line:
            if current_element:
                elements.append(current_element)
                current_element = {}
            if "Begin Object" in line:
                class_match = re.search(r'Class=(\S+)', line)
                name_match = re.search(r'Name=""(\S+)""', line)
                export_path_match = re.search(r'ExportPath=""(\S+)""', line)
                if class_match:
                    current_element['Class'] = class_match.group(1)
                if name_match:
                    current_element['Name'] = name_match.group(1)
                if export_path_match:
                    current_element['ExportPath'] = export_path_match.group(1)
        else:
            key_value_match = re.match(r'\s*(\S+)=\((.*)\)', line)
            if key_value_match:
                key = key_value_match.group(1)
                value = key_value_match.group(2)
                current_element[key] = value
    logging.info(f"Extracted {len(elements)} blueprint elements.")
    return elements

def blueprint_elements_to_code(elements):
    """
    Converts structured blueprint elements back into raw blueprint code.
    """
    blueprint_code = ""
    for element in elements:
        blueprint_code += "Begin Object "
        if 'Class' in element:
            blueprint_code += f"Class={element['Class']} "
        if 'Name' in element:
            blueprint_code += f'Name="{element["Name"]}" '
        if 'ExportPath' in element:
            blueprint_code += f'ExportPath="{element["ExportPath"]}"\n'
        for key, value in element.items():
            if key not in ['Class', 'Name', 'ExportPath']:
                blueprint_code += f"   {key}=({value})\n"
        blueprint_code += "End Object\n"
    logging.info("Converted blueprint elements back to code.")
    return blueprint_code

def read_and_process_blueprints_from_csv():
    """
    Reads blueprints from a CSV file, processes the data, and returns structured blueprint elements.
    """
    filename = f"./blueprints/blueprints_data.csv"
    df = read_csv(filename)
    if df is None:
        return None

    df['code'] = df['code'].str.strip()  # Remove leading/trailing whitespace
    df.dropna(subset=['code'], inplace=True)  # Remove rows where 'code' is missing

    df['elements'] = df['code'].apply(extract_blueprint_elements)

    logging.info("Processed blueprints from CSV.")
    return df

def save_blueprints_to_json(processed_blueprints):
    """
    Saves processed blueprints to a JSON file, ensuring no duplicate items are added.
    """
    if processed_blueprints is None:
        logging.error("No processed blueprints to save.")
        return

    output_filename = f"./blueprints/processed_blueprints.json"
    try:
        # Convert DataFrame to a list of dictionaries and remove duplicates
        records = processed_blueprints.to_dict('records')
        unique_records = [dict(t) for t in {tuple(d.items()) for d in records}]
        
        with open(output_filename, 'w') as f:
            json.dump(unique_records, f, indent=4)
        
        logging.info(f"Processed blueprints saved to {output_filename} with no duplicates")
    except Exception as e:
        logging.error(f"Failed to save processed blueprints to JSON: {e}")

if __name__ == "__main__":
    processed_blueprints = read_and_process_blueprints_from_csv()

    save_blueprints_to_json(processed_blueprints)
