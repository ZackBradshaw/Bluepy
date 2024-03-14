import requests
from bs4 import BeautifulSoup
import json
import os

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
    blueprint_links = []
    while url:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        blueprint_links.extend([link['href'] for link in links if '/blueprint/' in link['href']])
        next_page = soup.find('a', {'rel': 'next'})
        url = next_page['href'] if next_page else None
    return list(set(blueprint_links))  # Remove duplicates

def scrape_blueprint_data(link):
    """
    Scrapes blueprint data from a single link, including the blueprint code.
    """
    full_url = f"{BASE_URL}{link}"
    response = requests.get(full_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('title').text
    author = soup.find('meta', {'name': 'author'})['content'] if soup.find('meta', {'name': 'author'}) else 'anonymous'
    ue_version = soup.find(string='UE version').findNext('span').text if soup.find(string='UE version') else 'Unknown'
    # Extracting blueprint code
    blueprint_code = soup.find('pre', {'class': 'prettyprint'}).text if soup.find('pre', {'class': 'prettyprint'}) else "No code available"
    return {'title': title, 'author': author, 'ue_version': ue_version, 'url': full_url, 'code': blueprint_code}

def save_blueprint_md(blueprint_data):
    """
    Saves the blueprint data as a Markdown file in the ./blueprints/ directory.
    """
    directory = "./blueprints/"
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = f"{directory}{blueprint_data['title'].replace('/', '_').replace(' ', '_')}.md"
    with open(filename, 'w') as f:
        f.write(f"# {blueprint_data['title']}\n\n")
        f.write(f"**Author:** {blueprint_data['author']}\n")
        f.write(f"**UE Version:** {blueprint_data['ue_version']}\n")
        f.write(f"**URL:** {blueprint_data['url']}\n\n")
        f.write("## Blueprint Code\n")
        f.write("```ue4\n")  # Assuming the code is in UE4 syntax for syntax highlighting
        f.write(blueprint_data['code'])
        f.write("\n```\n")

def scrape_all_blueprints():
    """
    Scrapes all blueprints across all categories, saves each as a Markdown file.
    """
    categories = get_categories()
    all_blueprints_data = []
    for category in categories:
        blueprint_links = get_blueprint_links(f"{BASE_URL}{category}")
        for link in blueprint_links:
            blueprint_data = scrape_blueprint_data(link)
            save_blueprint_md(blueprint_data)
            all_blueprints_data.append(blueprint_data)
    return all_blueprints_data

if __name__ == "__main__":
    all_blueprints_data = scrape_all_blueprints()
    print(f"Scraped and saved {len(all_blueprints_data)} blueprints from all categories.")