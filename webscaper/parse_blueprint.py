import json
import pandas as pd
import re

def read_csv(csv_path):
    df = pd.read_csv(csv_path)
    return df

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
    return blueprint_code

def read_and_process_blueprints_from_csv(category_name):
    """
    Reads blueprints from a CSV file for a given category, processes the data, and returns structured blueprint elements.
    """
    filename = f"./blueprints/{category_name}_blueprints_data.csv"
    df = pd.read_csv(filename)

    df['code'] = df['code'].str.strip()  # Remove leading/trailing whitespace
    df.dropna(subset=['code'], inplace=True)  # Remove rows where 'code' is missing

    df['elements'] = df['code'].apply(extract_blueprint_elements)

    return df

def save_blueprints_to_json(processed_blueprints, category_name):
    """
    Saves processed blueprints to a JSON file.
    """
    output_filename = f"./blueprints/{category_name}_processed_blueprints.json"

    processed_blueprints.to_json(output_filename, orient='records', lines=True)

    print(f"Processed blueprints saved to {output_filename}")

if __name__ == "__main__":
    category_name = "example_category"  # Example category name
    processed_blueprints = read_and_process_blueprints_from_csv(category_name)

    save_blueprints_to_json(processed_blueprints, category_name)
