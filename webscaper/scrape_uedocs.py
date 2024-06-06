import requests
from bs4 import BeautifulSoup
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging configuration
logging.basicConfig(filename='unreal_docs.log', level=logging.INFO, filemode='w')

def setup_driver():
    """
    Sets up the Chrome WebDriver with headless options.
    """
    options = ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def fetch_page_content(url):
    """
    Fetches the HTML content of a given URL using Selenium WebDriver.
    """
    driver = setup_driver()
    try:
        driver.get(url)
        time.sleep(20)  # Increase wait time
        content = driver.page_source
        return content
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}", exc_info=True)  # Log traceback
    finally:
        driver.quit()

def parse_html(content, url):
    """
    Parses the HTML content to extract relevant text from specified tags.
    """
    soup = BeautifulSoup(content, 'html.parser')
    body_div = soup.find("div", {"id": "maincol"})
    if not body_div:
        logging.warning(f"Main content div not found in {url}")
        return None
    elements = body_div.find_all(['p', 'h1', 'h2', 'h3', 'pre'])  # Include 'pre' for code blocks
    texts = [re.sub(r'\s+', ' ', e.get_text().strip()) for e in elements]
    return '\n\n'.join(texts) + '\n\n'

def process_page(url):
    """
    Processes a single page: fetches content and parses it.
    """
    content = fetch_page_content(url)
    if content:
        return parse_html(content, url)
    return None

def main():
    """
    Main function to process a list of URLs concurrently and save the extracted text to a file.
    """
    # Hardcoded URLs for Unreal Engine documentation versions
    page_urls = [
        "https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-2-documentation?application_version=5.2",
        "https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-1-documentation?application_version=5.1",
        "https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-3-documentation?application_version=5.3"
    ]

    docs_text = ''
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_page, url): url for url in page_urls}
        for future in as_completed(futures):
            result = future.result()
            if result:
                docs_text += result
                logging.info(f"Successfully processed {futures[future]}")

    try:
        with open('unreal_docs.txt', 'w', encoding='utf-8') as f:
            f.write(docs_text)
            logging.info("Successfully wrote all pages to file.")
    except OSError as e:
        logging.error(f"Error writing to file: {e}")

if __name__ == '__main__':
    main()