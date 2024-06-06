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
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
import json
import base64
from io import BytesIO

# Setup enhanced logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://blueprintue.com"
SEARCH_URL = f"{BASE_URL}/search/?"

options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# TODO fix panning
# def pan_to_center_view(center_x, center_y):
#     try:
#         # Calculate the translation values to pan to the center
#         translate_x = center_x - 0  # Assuming the current view center x-coordinate is 0
#         translate_y = center_y - 0  # Assuming the current view center y-coordinate is 0
        
#         # Apply the translation to pan the view
#         # Update the view to center around the specified coordinates
        
#         logging.debug(f"Panned view to center around X: {center_x}, Y: {center_y}")
#     except Exception as e:
#         logging.error(f"Error panning view to center: {e}")

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

        # Adjust the view to ensure all blueprint nodes are within view
        # adjust_blueprint_view(driver.page_source)

        screenshot_path = f"./screenshots/{link.split('/')[-1]}{capture_blueprint_image.counter}.png"
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
        future_to_url = {executor.submit(fetch_links_for_page, url):
         url for url in page_urls}
        for future in as_completed(future_to_url):
            page_links = future.result()
            if page_links:
                blueprint_links.extend(page_links)
                logging.info(f"Scraped {len(page_links)} links from {future_to_url[future]}")

    return list(set(blueprint_links))  # Remove duplicates

def scrape_blueprint_data(link, session, all_blueprints_data):
    try:
        full_url = f"{BASE_URL}{link}"
        response = session.get(full_url)
        
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
            
            # Append the formatted data to the list
            all_blueprints_data.append(formatted_data)
            logging.info(f"Formatted data for {link}")
        else:
            logging.error(f"Failed to capture image for {link}")

    except Exception as e:
        logging.error(f"Error scraping blueprint data from {link}: {e}")

def format_data(image_path, metadata, blueprint_code):
    # Create the formatted data
    data = {
        "id": "",
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

    # Save the formatted JSON data
    json_path = f"data_{link.split('/')[-1]}.json"
    with open(json_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    
    return data

def save_blueprints_json(all_blueprints_data, filename='all_blueprints.json'):
    try:
        with open(filename, 'w') as f:
            json.dump(all_blueprints_data, f, indent=4)
            logging.info(f"Blueprint data saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving blueprint data to {filename}: {e}")


# Main execution
if __name__ == "__main__":
    blueprint_links = get_blueprint_links_concurrently(BASE_URL, 1, 10)
    
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    all_blueprints_data = []
    for link in blueprint_links:
        scrape_blueprint_data(link, session, all_blueprints_data)
    
    logging.debug(f"Number of blueprints to save: {len(all_blueprints_data)}")
    
    if all_blueprints_data:
        save_blueprints_json(all_blueprints_data)
        logging.info("Blueprint data saved successfully.")
    else:
        logging.warning("No blueprints to save.")
    
    driver.quit()