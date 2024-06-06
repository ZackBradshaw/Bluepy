import socket
import requests
from bs4 import BeautifulSoup
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
import json

# Setup enhanced logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://blueprintue.com"
DATA_FILE_PATH = "./blueprints/data.json"

options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def capture_blueprint_image(link):
    try:
        full_url = f"{BASE_URL}{link}"
        
        # Check if the domain name can be resolved
        try:
            socket.gethostbyname("blueprintue.com")
        except socket.gaierror as e:
            logging.error(f"Error resolving domain name: {e}")
            return None

        driver.get(full_url)
        # Wait for the blueprint to load
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#blueprint-render-playground'))) 
        
        # Attempt to click the fullscreen button if available
        try:
            fullscreen_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.frame-header__buttons-fullscreen')))
            fullscreen_button.click()
        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"Fullscreen button not found or not clickable for {link}: {e}")
            return None

        time.sleep(2)  # Wait for the transition to fullscreen

        # Attempt to click the reset button if available
        try:
            reset_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.frame-header__buttons-reset')))
            reset_button.click()
        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"Reset button not found or not clickable for {link}: {e}")
            return None

        time.sleep(2)  # Wait for the reset to complete

        screenshot_path = f"./screenshots/{link.split('/')[-1]}_{capture_blueprint_image.counter}.png"
        capture_blueprint_image.counter += 1
        directory = os.path.dirname(screenshot_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        driver.save_screenshot(screenshot_path)
        logging.info(f"Captured screenshot for {link}")

        return screenshot_path

    except Exception as e:
        logging.error(f"Error capturing blueprint from {link}: {e}")
        return None
            
# Initialize the counter attribute
capture_blueprint_image.counter = 1

def fetch_links_for_page(page_url):
    try:
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        response = session.get(page_url, timeout=10)
        if response.status_code != 200:
            logging.warning(f"Non-200 status code received: {response.status_code}")
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        session.close()  # Close the session after use
        return [link['href'] for link in links if '/blueprint/' in link['href']]
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching blueprint links from {page_url}: {e}")
        return []

def get_blueprint_links_concurrently(base_url, total_pages):
    """
    Fetches blueprint links across multiple pages concurrently.
    """
    page_urls = [f"{base_url}/last-blueprints/{page}/" for page in range(1, total_pages + 1)]
    blueprint_links = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch_links_for_page, url): url for url in page_urls}
        for future in as_completed(future_to_url):
            page_links = future.result()
            if page_links:
                blueprint_links.extend(page_links)
                logging.info(f"Scraped {len(page_links)} links from {future_to_url[future]}")

    return list(set(blueprint_links))  # Remove duplicates

def scrape_blueprint_data(link, session, data_file_path):
    try:
        full_url = f"{BASE_URL}{link}"
        response = session.get(full_url, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"Skipping {link}, received status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.find('title').text.strip()
        author = soup.find('meta', {'name': 'author'})['content'].strip() if soup.find('meta', {'name': 'author'}) else 'Anonymous'
        ue_version = soup.find(string='UE version').findNext('span').text.strip() if soup.find(string='UE version') else 'Unknown'
        
        # Extract blueprint code from a textarea with id="code_to_copy"
        blueprint_code = soup.find('textarea', {'id': 'code_to_copy'}).text.strip() if soup.find('textarea', {'id': 'code_to_copy'}) else "No code available"
        
        # Capture an image of the blueprint
        image_path = capture_blueprint_image(link)
        
        if image_path:
            # Format the data
            metadata = f"{title} by {author}, UE Version: {ue_version}"
            formatted_data = format_data(image_path, metadata, blueprint_code, link.split('/')[-1])
            
            # Append the formatted data to the file
            append_data_to_file(formatted_data, data_file_path)
            logging.info(f"Formatted data for {link}")
        else:
            logging.error(f"Failed to capture image for {link}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error scraping blueprint data from {link}: {e}")

def format_data(image_path, metadata, blueprint_code, link):
    # Create the formatted data
    data = {
        "id": link,
        "image": image_path,
        "conversations": [
            {
                "from": "human",
                "value": metadata,
            },
            {
                "from": "gpt",
                "value": blueprint_code,
            }
        ]
    }
    return data

def append_data_to_file(data, filename):
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = []

        existing_data.append(data)

        # Ensure the directory exists
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(filename, 'w') as f:
            json.dump(existing_data, f, indent=4)
            logging.info(f"Appended blueprint data to {filename}")
    except Exception as e:
        logging.error(f"Error appending blueprint data to {filename}: {e}")

# Main execution
if __name__ == "__main__":
    total_pages = 4777
    logging.info(f"Total pages to scrape: {total_pages}")
    
    blueprint_links = get_blueprint_links_concurrently(BASE_URL, total_pages)
    
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    for link in blueprint_links:
        scrape_blueprint_data(link, session, DATA_FILE_PATH)
    
    driver.quit()




