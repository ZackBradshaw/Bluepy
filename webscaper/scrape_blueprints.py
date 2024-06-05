import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Setup enhanced logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://blueprintue.com"
SEARCH_URL = f"{BASE_URL}/search/?"

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def fetch_links_for_page(page_url):
    try:
        response = requests.get(page_url)
        if response.status_code != 200:
            logging.warning(f"Non-200 status code received: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        return [link['href'] for link in links if '/blueprint/' in link['href']]
    except Exception as e:
        logging.error(f"Error fetching blueprint links from {page_url}: {e}")
        return []

def get_blueprint_links_concurrently(base_url, start_page=1, end_page=10):
    """
    Fetches blueprint links across multiple pages concurrently.
    """
    page_urls = [f"{base_url}page={page}" for page in range(start_page, end_page + 1)]
    blueprint_links = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch_links_for_page, url): url for url in page_urls}
        for future in as_completed(future_to_url):
            page_links = future.result()
            if page_links:
                blueprint_links.extend(page_links)
                logging.info(f"Scraped {len(page_links)} links from {future_to_url[future]}")

    return list(set(blueprint_links))  # Remove duplicates

def scrape_blueprint_data(link):
    """
    Scrapes blueprint data from a single link, including the blueprint code.
    """
    try:
        full_url = f"{BASE_URL}{link}"
        response = requests.get(full_url)
        if response.status_code != 200:
            logging.warning(f"Skipping {link}, received status code: {response.status_code}")
            return {}

        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title').text.strip()
        author = soup.find('meta', {'name': 'author'})['content'].strip() if soup.find('meta', {'name': 'author'}) else 'Anonymous'
        ue_version = soup.find(string='UE version').findNext('span').text.strip() if soup.find(string='UE version') else 'Unknown'
        
        # Extract blueprint code from a textarea with id="code_to_copy"
        blueprint_code = soup.find('textarea', {'id': 'code_to_copy'}).text.strip() if soup.find('textarea', {'id': 'code_to_copy'}) else "No code available"
        
        return {'title': title, 'author': author, 'ue_version': ue_version, 'url': full_url, 'code': blueprint_code}
    except Exception as e:
        logging.error(f"Error scraping blueprint data from {link}: {e}")
        return {}

def read_processed_blueprints_json(json_path):
    """
    Reads a JSON file containing processed blueprints and returns the data.
    """
    if not os.path.exists(json_path):
        logging.error(f"JSON file {json_path} does not exist.")
        return None
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        logging.info(f"JSON file {json_path} successfully read.")
        return data
    except Exception as e:
        logging.error(f"Failed to read JSON file {json_path}: {e}")
        return None

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

def scrape_blueprint_data_concurrently(blueprint_links):
    """
    Scrapes blueprint data from the links concurrently.
    """
    all_blueprints_data = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_link = {executor.submit(scrape_blueprint_data, link): link for link in blueprint_links}
        for future in as_completed(future_to_link):
            blueprint_data = future.result()
            if blueprint_data:
                all_blueprints_data.append(blueprint_data)
                logging.info(f"Scraped data for {future_to_link[future]}")

    return all_blueprints_data

def parse_json_back_to_code(json_path):
    """
    Reads processed blueprints from a JSON file and parses them back into raw blueprint code.
    """
    processed_blueprints = read_processed_blueprints_json(json_path)
    if processed_blueprints is None:
        logging.error("Failed to read processed blueprints from JSON.")
        return

    all_blueprint_codes = []
    for blueprint in processed_blueprints:
        elements = blueprint.get('elements', [])
        blueprint_code = blueprint_elements_to_code(elements)
        all_blueprint_codes.append(blueprint_code)

    # Here you can save the blueprint codes back to a file or process them further as needed
    logging.info(f"Parsed {len(all_blueprint_codes)} blueprints back into code.")

def capture_full_blueprint(link):
    """
    Captures the full blueprint by navigating, zooming, and panning to ensure all nodes are visible.
    """
    try:
        full_url = f"{BASE_URL}{link}"
        driver.get(full_url)
        # Wait for the blueprint to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'blueprint')))

        # Fullscreen the blueprint
        fullscreen_button = driver.find_element(By.CLASS_NAME, 'fullscreen')
        fullscreen_button.click()
        time.sleep(2)  # Wait for the transition to fullscreen

        # Zoom out to ensure all nodes are visible
        body = driver.find_element(By.TAG_NAME, 'body')
        for _ in range(10):  # Adjust the range as needed
            body.send_keys(Keys.CONTROL, Keys.SUBTRACT)
            time.sleep(0.1)

        # Pan to ensure all nodes are in view
        blueprint_area = driver.find_element(By.CLASS_NAME, 'blueprint')
        actions = webdriver.ActionChains(driver)
        actions.move_to_element(blueprint_area).click_and_hold().move_by_offset(-500, -500).release().perform()
        time.sleep(2)  # Wait for the panning to complete

        # Take a screenshot
        screenshot_path = f"./screenshots/{link.split('/')[-1]}.png"
        directory = os.path.dirname(screenshot_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        driver.save_screenshot(screenshot_path)
        logging.info(f"Captured screenshot for {link}")

    except Exception as e:
        logging.error(f"Error capturing blueprint from {link}: {e}")

def scrape_all_blueprints_concurrently():
    """
    Scrapes all blueprints concurrently and saves the data into a CSV file.
    """
    logging.info("Starting to scrape all blueprints concurrently...")
    blueprint_links = get_blueprint_links_concurrently(SEARCH_URL, 4000, 4075)  # Example: Scrape pages 4000 to 4075
    all_blueprints_data = scrape_blueprint_data_concurrently(blueprint_links)
    save_blueprints_csv(all_blueprints_data)

    # Capture screenshots of all blueprints
    for link in blueprint_links:
        capture_full_blueprint(link)

if __name__ == "__main__":
    scrape_all_blueprints_concurrently()
    driver.quit()