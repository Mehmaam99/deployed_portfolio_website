import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse
import os
from datetime import datetime

# Configure logging - use /tmp if local logs are not writable (common in cloud deployments)
log_dir = "logs"
try:
    os.makedirs(log_dir, exist_ok=True)
except PermissionError:
    log_dir = "/tmp/logs"
    os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"scraper_{datetime.now().strftime('%Y%m%d')}.log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def scrape_single_page(url: str) -> str:
    """
    Scrapes a single page and returns cleaned text.
    """
    try:
        logger.info(f"Starting scrape for: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Successfully fetched {url} - Status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
            
        text = soup.get_text(separator=' ')
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        logger.info(f"Extracted {len(cleaned_text)} characters from {url}")
        return cleaned_text
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}", exc_info=True)
        return ""

def scrape_website(base_url: str = "https://syedmuhammadmehmam.site/") -> str:
    """
    Scrapes the main page of Syed Muhammad Mehmam's portfolio.
    Returns cleaned text content.
    Also saves the page to a file.
    """
    logger.info("=" * 60)
    logger.info("Starting website scraping session")
    logger.info(f"Base URL: {base_url}")
    logger.info("=" * 60)
    
    # Create directory for scraped pages
    pages_dir = "scraped_pages"
    try:
        os.makedirs(pages_dir, exist_ok=True)
    except PermissionError:
        pages_dir = "/tmp/scraped_pages"
        os.makedirs(pages_dir, exist_ok=True)
    
    # List of pages to scrape (assuming single page portfolio)
    pages_to_scrape = [
        "",  # Homepage
    ]
    
    all_content = []
    successful_pages = 0
    failed_pages = 0
    
    for page in pages_to_scrape:
        url = urljoin(base_url, page)
        logger.info(f"\n--- Scraping page {successful_pages + failed_pages + 1}/{len(pages_to_scrape)}: {url} ---")
        
        content = scrape_single_page(url)
        if content:
            all_content.append(f"=== Content from {url} ===\n{content}\n")
            successful_pages += 1
            
            # Save individual page to file
            page_name = page if page else "homepage"
            safe_filename = page_name.replace("/", "_")
            file_path = os.path.join(pages_dir, f"{safe_filename}.txt")
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"URL: {url}\n")
                    f.write(f"Scraped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Characters: {len(content)}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(content)
                logger.info(f"✓ Saved page content to: {file_path}")
            except Exception as e:
                logger.error(f"Failed to save page to file: {e}")
        else:
            failed_pages += 1
            logger.warning(f"✗ Failed to scrape {url}")
    
    combined_content = "\n\n".join(all_content)
    
    logger.info("\n" + "=" * 60)
    logger.info("Scraping session complete")
    logger.info(f"Total pages scraped: {successful_pages}/{len(pages_to_scrape)}")
    logger.info(f"Failed pages: {failed_pages}")
    logger.info(f"Total characters: {len(combined_content)}")
    logger.info(f"Pages saved to: {os.path.abspath(pages_dir)}")
    logger.info(f"Log file: {os.path.abspath(log_file)}")
    logger.info("=" * 60)
    
    return combined_content

if __name__ == "__main__":
    print(scrape_website())


