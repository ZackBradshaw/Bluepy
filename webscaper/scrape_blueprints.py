import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://blueprintue.com"
CATEGORIES_URL = f"{BASE_URL}/"

def get_categories():
    """
    Fetches all blueprint categories from the main page.
    """
    try:
        response = requests.get(CATEGORIES_URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        categories = soup.find_all('a', href=True)
        category_links = [link['href'] for link in categories if '/type/' in link['href']]
        return list(set(category_links))  # Remove duplicates
    except Exception as e:
        logging.error(f"Error fetching categories: {e}")
        return []

def get_blueprint_links(url):
    """
    Extracts all blueprint links from the given category URL.
    """
    blueprint_links = []
    try:
        while url:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            blueprint_links.extend([link['href'] for link in links if '/blueprint/' in link['href']])
            next_page = soup.find('a', {'rel': 'next'})
            url = next_page['href'] if next_page else None
        return list(set(blueprint_links))  # Remove duplicates
    except Exception as e:
        logging.error(f"Error fetching blueprint links from {url}: {e}")
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
        # Extracting blueprint code
        blueprint_code = soup.find('pre', {'class': 'prettyprint'}).text if soup.find('pre', {'class': 'prettyprint'}) else "No code available"
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
        filename = "./blueprints/blueprints_data.csv"
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)
        df.to_csv(filename, index=False)
        logging.info(f"Saved {len(blueprints_data)} blueprints to {filename}")
    except Exception as e:
        logging.error(f"Error saving blueprints to CSV: {e}")

def scrape_all_blueprints():
    """
    Scrapes all blueprints across all categories and saves the data as a CSV file.
    """
    categories = get_categories()
    all_blueprints_data = []
    for category in categories:
        logging.info(f"Scraping category: {category}")
        blueprint_links = get_blueprint_links(f"{BASE_URL}{category}")
        for link in blueprint_links:
            blueprint_data = scrape_blueprint_data(link)
            blueprint_data = scrape_blueprint_data(link)
            if blueprint_data:  # Ensure we only add non-empty results
                all_blueprints_data.append(blueprint_data)
    save_blueprints_csv(all_blueprints_data)

if __name__ == "__main__":
    scrape_all_blueprints()