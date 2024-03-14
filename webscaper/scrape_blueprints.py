import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://blueprintue.com"
BLUEPRINTS_URL = f"{BASE_URL}/search/"

def get_blueprint_links():
    """
    Extracts all blueprint links from the blueprints page.
    """
    blueprint_links = []
    try:
        response = requests.get(BLUEPRINTS_URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        blueprint_links.extend([link['href'] for link in links if '/blueprint/' in link['href']])
        return list(set(blueprint_links))  # Remove duplicates
    except Exception as e:
        logging.error(f"Error fetching blueprint links: {e}")
        return []

def scrape_blueprint_data(link):
    """
    Scrapes blueprint data from a single link, including the blueprint code.
    """
    try:
        full_url = f"{BASE_URL}{link}"
        response = requests.get(full_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title').text
        author = soup.find('meta', {'name': 'author'})['content'] if soup.find('meta', {'name': 'author'}) else 'anonymous'
        ue_version = soup.find(string='UE version').findNext('span').text if soup.find(string='UE version') else 'Unknown'
        
        # Adjusted to extract blueprint code from a textarea with id="code_to_copy"
        blueprint_code = soup.find('textarea', {'id': 'code_to_copy'}).text if soup.find('textarea', {'id': 'code_to_copy'}) else "No code available"
        
        return {'title': title, 'author': author, 'ue_version': ue_version, 'url': full_url, 'code': blueprint_code}
    except Exception as e:
        logging.error(f"Error scraping blueprint data from {link}: {e}")
        return {}

def save_blueprints_csv(blueprints_data):
    """
    Saves the blueprint data as a CSV file.
    """
    try:
        df = pd.DataFrame(blueprints_data)
        filename = f"./blueprints/blueprints_data.csv"
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)
        df.to_csv(filename, index=False)
        logging.info(f"Saved {len(blueprints_data)} blueprints to {filename}")
    except Exception as e:
        logging.error(f"Error saving blueprints to CSV: {e}")

def scrape_all_blueprints():
    """
    Scrapes all blueprints and saves the data into a CSV file.
    """
    logging.info("Scraping all blueprints")
    blueprint_links = get_blueprint_links()
    all_blueprints_data = []
    for link in blueprint_links:
        blueprint_data = scrape_blueprint_data(link)
        if blueprint_data:  # Ensure we only add non-empty results
            all_blueprints_data.append(blueprint_data)
    save_blueprints_csv(all_blueprints_data)

if __name__ == "__main__":
    scrape_all_blueprints()
