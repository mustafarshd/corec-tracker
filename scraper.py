"""
Web scraper to extract facility usage data from Purdue RecWell website.
"""
import os
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
import requests
from bs4 import BeautifulSoup


class FacilityUsageScraper:
    def __init__(self, headless: bool = True):
        """
        Initialize the scraper.
        
        Args:
            headless: Run browser in headless mode (default: True)
        """
        self.headless = headless
        self.url = "https://www.purdue.edu/recwell/facility-usage/index.php"
        self.driver = None
    
    def _setup_driver(self):
        """Setup Selenium WebDriver."""
        import platform
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        # On Linux (e.g. Railway) use system Chromium if present
        if platform.system() == "Linux":
            for binary in ("/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome-stable"):
                if os.path.exists(binary):
                    chrome_options.binary_location = binary
                    break
            # Prefer system chromedriver on Linux (installed by nixpacks)
            chromedriver_path = os.environ.get("CHROMEDRIVER_PATH") or (
                "/usr/bin/chromedriver" if os.path.exists("/usr/bin/chromedriver") else None
            )
        else:
            chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
        try:
            if chromedriver_path and os.path.exists(chromedriver_path):
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            elif WEBDRIVER_MANAGER_AVAILABLE:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            print("Make sure ChromeDriver is installed and in your PATH")
            print("Or install webdriver-manager: pip install webdriver-manager")
            raise
    
    def _try_requests_first(self) -> Optional[List[Dict]]:
        """Try to get data using requests first (faster if possible)."""
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for facility data in the HTML
            # This will need to be adjusted based on actual page structure
            facilities = []
            
            # Try to find facility usage information
            # Common patterns: tables, divs with facility names, JSON data
            facility_elements = soup.find_all(['div', 'span', 'td'], 
                                             class_=re.compile(r'facility|usage|occupancy', re.I))
            
            if facility_elements:
                # If we find facility elements, try to extract data
                for elem in facility_elements:
                    text = elem.get_text(strip=True)
                    # Look for patterns like "CoRec: 45/200" or "45%"
                    match = re.search(r'(\d+)\s*/\s*(\d+)|(\d+)%', text)
                    if match:
                        if match.group(1) and match.group(2):
                            occupancy = int(match.group(1))
                            capacity = int(match.group(2))
                            percentage = (occupancy / capacity) * 100
                        else:
                            percentage = float(match.group(3))
                            occupancy = None
                            capacity = None
                        
                        # Try to extract facility name from nearby text
                        facility_name = self._extract_facility_name(elem)
                        
                        if facility_name:
                            facilities.append({
                                'name': facility_name,
                                'occupancy': occupancy,
                                'capacity': capacity,
                                'percentage': percentage,
                                'timestamp': datetime.now()
                            })
            
            return facilities if facilities else None
            
        except Exception as e:
            print(f"Requests method failed: {e}")
            return None
    
    def _extract_facility_name(self, element) -> Optional[str]:
        """Extract facility name from HTML element."""
        # Try to find facility name in parent elements or siblings
        parent = element.parent
        for _ in range(3):  # Check up to 3 levels up
            if parent:
                text = parent.get_text(strip=True)
                # Common facility names at Purdue
                facility_names = ['CoRec', 'Corec', 'TREC', 'Trec', 'Boiler', 'Aquatics']
                for name in facility_names:
                    if name.lower() in text.lower():
                        return name
                parent = parent.parent
        return None
    
    def scrape_with_selenium(self) -> List[Dict]:
        """Scrape facility usage data using Selenium (for dynamic content)."""
        if not self.driver:
            self._setup_driver()
        
        facilities = []
        
        try:
            print(f"Loading page: {self.url}")
            self.driver.get(self.url)
            
            # Wait for page to load and dynamic content to appear
            print("Waiting for page to load...")
            time.sleep(10)  # Give more time for JavaScript to load
            
            # Wait for any iframes to load
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except TimeoutException:
                print("Page took longer than expected to load")
            
            # Check for iframes first (common for embedded widgets)
            print("Checking for iframes...")
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Found {len(iframes)} iframes")
            
            for i, iframe in enumerate(iframes):
                try:
                    print(f"Switching to iframe {i+1}...")
                    self.driver.switch_to.frame(iframe)
                    time.sleep(3)  # Wait for iframe content
                    
                    # Try to find data in iframe
                    iframe_facilities = self._find_in_tables()
                    iframe_facilities.extend(self._find_in_divs())
                    if not iframe_facilities:
                        # Look for any text containing numbers and percentages
                        body_text = self.driver.find_element(By.TAG_NAME, "body").text
                        if body_text and ("%" in body_text or "/" in body_text):
                            print(f"Iframe {i+1} contains data-like content")
                            iframe_facilities = self._parse_all_text(body_text)
                    
                    if iframe_facilities:
                        facilities.extend(iframe_facilities)
                        print(f"Found {len(iframe_facilities)} facilities in iframe {i+1}")
                    
                    self.driver.switch_to.default_content()
                except Exception as e:
                    print(f"Error processing iframe {i+1}: {e}")
                    self.driver.switch_to.default_content()
            
            # If no data found in iframes, check main page
            if not facilities:
            
                # Try multiple strategies to find facility data
                print("Searching main page content...")
                strategies = [
                    self._find_in_tables,
                    self._find_in_divs,
                    self._find_json_data,
                ]
                
                for strategy in strategies:
                    try:
                        found = strategy()
                        if found:
                            facilities.extend(found)
                            print(f"Found {len(found)} facilities using {strategy.__name__}")
                    except Exception as e:
                        print(f"Strategy {strategy.__name__} failed: {e}")
                        continue
                
                # Last resort: parse all visible text
                if not facilities:
                    print("Trying to parse all visible text...")
                    try:
                        body_text = self.driver.find_element(By.TAG_NAME, "body").text
                        facilities = self._parse_all_text(body_text)
                    except Exception as e:
                        print(f"Error parsing body text: {e}")
            
            if not facilities:
                print("Warning: No facility data found. Page structure may have changed.")
                # Save page source for debugging
                try:
                    with open("page_source_debug.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    print("Page source saved to page_source_debug.html for inspection")
                except Exception as e:
                    print(f"Could not save page source: {e}")
        
        except Exception as e:
            print(f"Error scraping with Selenium: {e}")
        
        return facilities
    
    def _find_in_tables(self) -> List[Dict]:
        """Find facility data in HTML tables."""
        facilities = []
        try:
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        text = row.text
                        facility_data = self._parse_facility_text(text)
                        if facility_data:
                            facilities.append(facility_data)
        except Exception as e:
            print(f"Error finding tables: {e}")
        return facilities
    
    def _find_in_divs(self) -> List[Dict]:
        """Find facility data in div elements."""
        facilities = []
        try:
            # Look for the specific RecWell widget structure
            location_divs = self.driver.find_elements(By.CSS_SELECTOR, ".rw-c2c-feed__location")
            
            for location_div in location_divs:
                try:
                    # Extract facility name
                    name_elem = location_div.find_element(By.CSS_SELECTOR, ".rw-c2c-feed__location--name")
                    facility_name = name_elem.text.strip()
                    
                    # Extract capacity information
                    capacity_elem = location_div.find_element(By.CSS_SELECTOR, ".rw-c2c-feed__about--capacity")
                    capacity_text = capacity_elem.text.strip()
                    
                    # Parse capacity text like "Capacity: 1/10 // 10%"
                    # or "Capacity: 45/200 // 22.5%"
                    match = re.search(r'Capacity:\s*(\d+)\s*/\s*(\d+)\s*//\s*([\d.]+)%', capacity_text)
                    if match:
                        occupancy = int(match.group(1))
                        capacity = int(match.group(2))
                        percentage = float(match.group(3))
                        
                        facilities.append({
                            'name': facility_name,
                            'occupancy': occupancy,
                            'capacity': capacity,
                            'percentage': percentage,
                            'timestamp': datetime.now()
                        })
                        print(f"Found facility: {facility_name} - {occupancy}/{capacity} ({percentage}%)")
                
                except NoSuchElementException:
                    continue
                except Exception as e:
                    print(f"Error parsing location div: {e}")
                    continue
            
            # If no RecWell widgets found, try generic selectors
            if not facilities:
                selectors = [
                    "[class*='facility']",
                    "[class*='usage']",
                    "[class*='occupancy']",
                    "[id*='facility']",
                    "[id*='usage']"
                ]
                
                for selector in selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text
                        facility_data = self._parse_facility_text(text)
                        if facility_data:
                            facilities.append(facility_data)
        except Exception as e:
            print(f"Error finding divs: {e}")
        return facilities
    
    def _find_json_data(self) -> List[Dict]:
        """Look for JSON data embedded in the page."""
        facilities = []
        try:
            # Look for script tags with JSON data
            scripts = self.driver.find_elements(By.TAG_NAME, "script")
            for script in scripts:
                content = script.get_attribute("innerHTML")
                if content and ("facility" in content.lower() or "usage" in content.lower()):
                    # Try to extract JSON
                    import json
                    json_matches = re.findall(r'\{[^{}]*"facility"[^{}]*\}', content, re.IGNORECASE)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            # Process JSON data
                            if 'name' in data or 'facility' in data:
                                facilities.append(self._convert_json_to_facility(data))
                        except:
                            pass
        except Exception as e:
            print(f"Error finding JSON: {e}")
        return facilities
    
    def _parse_all_text(self, text: str) -> List[Dict]:
        """Parse facility data from a large text block."""
        facilities = []
        lines = text.split('\n')
        
        facility_names = ['CoRec', 'Corec', 'TREC', 'Trec', 'Boiler', 'Aquatics', 
                         'Cordova', 'Recreation', 'Fitness', 'Facility']
        
        current_facility = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line contains a facility name
            for name in facility_names:
                if name.lower() in line.lower():
                    current_facility = name
                    break
            
            # Try to parse occupancy data from the line
            if current_facility:
                facility_data = self._parse_facility_text(line)
                if facility_data and facility_data.get('name'):
                    facilities.append(facility_data)
                    current_facility = None  # Reset after finding data
        
        return facilities
    
    def _parse_facility_text(self, text: str) -> Optional[Dict]:
        """Parse facility data from text string."""
        # Common patterns:
        # "CoRec: 45/200 (22.5%)"
        # "CoRec - 45 people / 200 capacity"
        # "45%"
        
        facility_names = ['CoRec', 'Corec', 'TREC', 'Trec', 'Boiler', 'Aquatics', 
                         'Cordova', 'Recreation', 'Fitness']
        
        facility_name = None
        for name in facility_names:
            if name.lower() in text.lower():
                facility_name = name
                break
        
        if not facility_name:
            return None
        
        # Extract numbers
        # Pattern 1: "45/200"
        match = re.search(r'(\d+)\s*/\s*(\d+)', text)
        if match:
            occupancy = int(match.group(1))
            capacity = int(match.group(2))
            percentage = (occupancy / capacity) * 100
            return {
                'name': facility_name,
                'occupancy': occupancy,
                'capacity': capacity,
                'percentage': percentage,
                'timestamp': datetime.now()
            }
        
        # Pattern 2: "45%" or "22.5%"
        match = re.search(r'(\d+\.?\d*)%', text)
        if match:
            percentage = float(match.group(1))
            return {
                'name': facility_name,
                'occupancy': None,
                'capacity': None,
                'percentage': percentage,
                'timestamp': datetime.now()
            }
        
        return None
    
    def _convert_json_to_facility(self, data: dict) -> dict:
        """Convert JSON data to facility format."""
        name = data.get('name') or data.get('facility') or 'Unknown'
        occupancy = data.get('occupancy') or data.get('current')
        capacity = data.get('capacity') or data.get('max')
        percentage = data.get('percentage') or data.get('percent')
        
        if occupancy and capacity:
            if not percentage:
                percentage = (occupancy / capacity) * 100
        
        return {
            'name': name,
            'occupancy': occupancy,
            'capacity': capacity,
            'percentage': percentage,
            'timestamp': datetime.now()
        }
    
    def scrape(self) -> List[Dict]:
        """
        Scrape facility usage data.
        Tries requests first, falls back to Selenium if needed.
        """
        # Try requests first (faster)
        facilities = self._try_requests_first()
        
        if not facilities:
            # Fall back to Selenium for dynamic content
            print("Using Selenium to scrape dynamic content...")
            facilities = self.scrape_with_selenium()
        
        return facilities or []
    
    def close(self):
        """Close the browser driver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
