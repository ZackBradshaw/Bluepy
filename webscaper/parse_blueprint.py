import openai
import json
import pandas as pd

openai.api_key = 'your_openai_api_key_here'

def read_and_clean_blueprints_from_csv(category_name):
    """
    Reads blueprints from a CSV file for a given category, cleans the data, and returns unique blueprint codes.
    """
    filename = f"./blueprints/{category_name}_blueprints_data.csv"
    df = pd.read_csv(filename)
    
    # Example cleaning steps (adjust based on actual data needs)
    df['code'] = df['code'].str.strip()  # Remove leading/trailing whitespace
    df.dropna(subset=['code'], inplace=True)  # Remove rows where 'code' is missing
    
    unique_blueprints = df.drop_duplicates(subset=['code'])
    return unique_blueprints

def blueprint_code_to_template(blueprint_code):
    """
    Converts blueprint code into a structured template.
    """
    # This is a simplified example. The actual implementation would need to handle the specific structure of the blueprint code.
    template = blueprint_code.replace("Begin Object", "🚀 Begin Object")\
                              .replace("End Object", "🛑 End Object")\
                              .replace("CustomProperties Pin", "📌 CustomProperties Pin")
    return template

def process_and_update_blueprint_code(unique_blueprints):
    """
    Processes each unique blueprint to update its 'code' column.
    """
    for index, row in unique_blueprints.iterrows():
        updated_code = blueprint_code_to_template(row['code'])
        unique_blueprints.at[index, 'code'] = updated_code
    return unique_blueprints

def save_blueprints_to_json(processed_blueprints, category_name):
    """
    Saves processed blueprints to a JSON file.
    """
    output_filename = f"./blueprints/{category_name}_processed_blueprints.json"
    processed_blueprints.to_json(output_filename, orient='records', lines=True)
    print(f"Processed blueprints saved to {output_filename}")

if __name__ == "__main__":
    category_name = "example_category"  # Example category name
    unique_blueprints = read_and_clean_blueprints_from_csv(category_name)
    processed_blueprints = process_and_update_blueprint_code(unique_blueprints)
    save_blueprints_to_json(processed_blueprints, category_name)
