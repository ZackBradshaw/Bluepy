import json
import pandas as pd
import re
import logging
import os

# Setup enhanced logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_csv(csv_path):
    """
    Reads a CSV file and returns a DataFrame.
    """
    try:
        df = pd.read_csv(csv_path)
        logging.info(f"CSV file {csv_path} successfully read.")
        return df
    except Exception as e:
        logging.error(f"Failed to read CSV file {csv_path}: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of failure

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

def read_and_process_blueprints_from_csv(csv_path):
    """
    Reads blueprints from a CSV file, processes the data, and returns structured blueprint elements.
    """
    df = read_csv(csv_path)

    df['code'] = df['code'].str.strip()  # Remove leading/trailing whitespace
    df.dropna(subset=['code'], inplace=True)  # Remove rows where 'code' is missing

    df['elements'] = df['code'].apply(extract_blueprint_elements)

    logging.info(f"Processed blueprints from {csv_path}.")
    return df

def save_blueprints_to_json(processed_blueprints, output_filename):
    """
    Saves processed blueprints to a JSON file.
    """
    output_path = f"./blueprints/processed_blueprints.json"

    processed_blueprints.to_json(output_path, orient='records', lines=True)

    logging.info(f"Processed blueprints saved to {output_path}")

if __name__ == "__main__":
    csv_path = "./blueprints/blueprints_data.csv"  # Example CSV path
    processed_blueprints = read_and_process_blueprints_from_csv(csv_path)

    output_filename = os.path.splitext(os.path.basename(csv_path))[0]  # Extract filename without extension
    save_blueprints_to_json(processed_blueprints, output_filename)
