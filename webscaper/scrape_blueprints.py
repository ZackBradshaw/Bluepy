import requests
from bs4 import BeautifulSoup
import json

BASE_URL = "https://blueprintue.com"
NIAGARA_TYPE_URL = f"{BASE_URL}/type/niagara/"

def get_blueprint_links(url):
    """
    Extracts all blueprint links from the given URL.
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
    # Example: Extract title and author, you can add more fields as needed
    title = soup.find('title').text
    author = soup.find('meta', {'name': 'author'})['content'] if soup.find('meta', {'name': 'author'}) else 'anonymous'
    return {'title': title, 'author': author, 'url': full_url}

def scrape_all_blueprints():
    """
    Scrapes all blueprints and returns them in a structured format.
    """
    blueprint_links = get_blueprint_links(NIAGARA_TYPE_URL)
    blueprints_data = [scrape_blueprint_data(link) for link in blueprint_links]
    return blueprints_data

if __name__ == "__main__":
    blueprints_data = scrape_all_blueprints()
    with open('blueprints_data.json', 'w') as f:
        json.dump(blueprints_data, f, indent=4)
    print(f"Scraped {len(blueprints_data)} blueprints.")