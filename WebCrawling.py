import time
import re
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def save_job_posting_to_txt(url, filename="job_posting.txt"):
    """
    Saves the content of a job posting to a txt file in the 'res' subfolder.
    """
    print(f"Current Python path: {sys.executable}")
    
    # 1. Create 'res' directory if it doesn't exist
    output_dir = "res"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # Set the full path for the file
    file_path = os.path.join(output_dir, filename)
    
    # 2. Chrome Options Setup
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # 3. Initialize Driver
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Driver initialization failed: {e}")
        return False

    try:
        print(f"Connecting to: {url}")
        driver.get(url)

        # 4. Wait for content to load
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Extra wait for Javascript rendering
        time.sleep(5)

        # 5. Parse Content
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unnecessary elements
        for tag in soup(["script", "style", "nav", "footer", "header", "button", "input", "meta", "noscript"]):
            tag.decompose()

        # 6. Extract and Clean Text
        text_content = soup.get_text(separator='\n')
        lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        clean_text = '\n'.join(lines)

        # 7. Save to File in 'res' folder
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"JOB POSTING SOURCE: {url}\n")
            f.write("="*60 + "\n\n")
            f.write(clean_text)
            
        print(f"Success! Saved to {file_path}")
        return True

    except Exception as e:
        print(f"Error during scraping: {e}")
        return False

    finally:
        driver.quit()

if __name__ == "__main__":
    test_url = "https://careers.nexon.com/recruit/9113" 
    save_job_posting_to_txt(test_url, "nexon_scraping_result.txt")
