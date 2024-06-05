import socket
import pyperclip
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# Setup enhanced logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://blueprintue.com"
SEARCH_URL = f"{BASE_URL}/search/?"

options = Options()
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def capture_blueprint_image(link):
    """
    Captures the full blueprint by navigating, zooming, and panning to ensure all nodes are visible.
    """
    try:
        full_url = f"{BASE_URL}{link}"
        
        # Check if the domain name can be resolved
        try:
            socket.gethostbyname("blueprintue.com")
        except socket.gaierror as e:
            logging.error(f"Error resolving domain name: {e}")
            return

        driver.get(full_url)
        # Wait for the blueprint to load
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'blueprint'))) 
        # Attempt to click the fullscreen button if available
        try:
            fullscreen_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'frame-header__buttons-fullscreen')]")))
            fullscreen_button.click()
        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"Fullscreen button not found or not clickable for {link}: {e}")
            return

        time.sleep(2)  # Wait for the transition to fullscreen

        # Attempt to click the reset button if available
        try:
            reset_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'frame-header__buttons-reset')]")))
            reset_button.click()
        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"Reset button not found or not clickable for {link}: {e}")
            return

        time.sleep(2)  # Wait for the reset to complete

        # Take a screenshot
        screenshot_path = f"./screenshots/{link.split('/')[-1]}.png"
        directory = os.path.dirname(screenshot_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        driver.save_screenshot(screenshot_path)
        logging.info(f"Captured screenshot for {link}")

    except Exception as e:
        logging.error(f"Error capturing blueprint from {link}: {e}")
        
def fetch_links_for_page(page_url):
    try:
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        response = session.get(page_url)
        if response.status_code != 200:
            logging.warning(f"Non-200 status code received: {response.status_code}")
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        session.close()  # Close the session after use
        return [link['href'] for link in links if '/blueprint/' in link['href']]
    except Exception as e:
        logging.error(f"Error fetching blueprint links from {page_url}: {e}")
        return []

def get_blueprint_links_concurrently(base_url, start_page=1, end_page=10):
    """
    Fetches blueprint links across multiple pages concurrently.
    """
    page_urls = [f"{base_url}/type/blueprint/{page}/" for page in range(start_page, end_page + 1)]
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
    Scrapes blueprint data from a single link, including the blueprint code and capturing an image.
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
        
        # Capture an image of the blueprint
        capture_blueprint_image(link)
        
        logging.debug(f"Connection pool size: {requests.Session().connection_pool}")
        response.close()
        
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
   
 
def parse_json_back_to_code(json_path):
    """
    Reads processed blueprints from a JSON file and parses them back into raw blueprint code.
    """
    processed_blueprints = read_processed_blueprints_json(json_path)
    if processed_blueprints is None:
        logging.error("Failed to read processed blueprints from JSON.")
        return []

    all_blueprint_codes = [blueprint['code'] for blueprint in processed_blueprints if 'code' in blueprint]
    logging.info(f"Parsed {len(all_blueprint_codes)} blueprints back into code.")
    return all_blueprint_codes

if __name__ == "__main__":
    blueprint_links = get_blueprint_links_concurrently(BASE_URL, 1, 10)
    all_blueprints_data = [scrape_blueprint_data(link) for link in blueprint_links]
    
    # Filter out empty blueprint data entries
    all_blueprints_data = [data for data in all_blueprints_data if data]
    
    logging.debug(f"Number of blueprints to save: {len(all_blueprints_data)}")
    
    if all_blueprints_data:
        save_blueprints_csv(all_blueprints_data)
    else:
        logging.warning("No blueprints to save.")
    
    driver.quit()