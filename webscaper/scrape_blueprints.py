import requests
from bs4 import BeautifulSoup
import json

BASE_URL = "https://blueprintue.com"
CATEGORIES_URL = f"{BASE_URL}/"

def get_categories():
    """
    Fetches all blueprint categories from the main page.
    """
    response = requests.get(CATEGORIES_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    categories = soup.find_all('a', href=True)
    category_links = [link['href'] for link in categories if '/type/' in link['href']]
    return list(set(category_links))  # Remove duplicates

def get_blueprint_links(url):
    """
    Extracts all blueprint links from the given category URL.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)
    blueprint_links = [link['href'] for link in links if '/blueprint/' in link['href']]
    return list(set(blueprint_links))  # Remove duplicates

def scrape_blueprint_data(link):
    """
    Scrapes blueprint data from a single link.
    """
    full_url = f"{BASE_URL}{link}"
    response = requests.get(full_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Example: Extract title, author, and UE version
    title = soup.find('title').text
    author = soup.find('meta', {'name': 'author'})['content'] if soup.find('meta', {'name': 'author'}) else 'anonymous'
    ue_version = soup.find(text='UE version').findNext('span').text if soup.find(text='UE version') else 'Unknown'
    return {'title': title, 'author': author, 'ue_version': ue_version, 'url': full_url}

def scrape_all_blueprints():
    """
    Scrapes all blueprints across all categories and returns them in a structured format.
    """
    categories = get_categories()
    all_blueprints_data = []
    for category in categories:
        blueprint_links = get_blueprint_links(f"{BASE_URL}{category}")
        blueprints_data = [scrape_blueprint_data(link) for link in blueprint_links]
        all_blueprints_data.extend(blueprints_data)
    return all_blueprints_data

if __name__ == "__main__":
    all_blueprints_data = scrape_all_blueprints()
    with open('all_blueprints_data.json', 'w') as f:
        json.dump(all_blueprints_data, f, indent=4)
    print(f"Scraped {len(all_blueprints_data)} blueprints from all categories.")