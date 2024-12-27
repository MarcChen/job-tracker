from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random


class JobScraper:
    def __init__(self, url):
        self.url = url
        self.driver = self._setup_driver()

    def _setup_driver(self):
        """Set up the Selenium WebDriver with necessary options."""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.binary_location = '/usr/bin/chromium'

        service = Service('/usr/bin/chromedriver')
        return webdriver.Chrome(service=service, options=chrome_options)

    def load_all_offers(self):
        """Load all offers by repeatedly clicking 'Voir Plus d'Offres' with added randomness."""
        self.driver.get(self.url)
        time.sleep(random.uniform(3, 6))  # Randomized initial wait

        previous_count = 0

        while True:
            try:
                # Check if the "Voir Plus d'Offres" button is still clickable
                button = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, "see-more-btn")))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", button)
                time.sleep(random.uniform(1, 2))  # Randomized scroll wait
                self.driver.execute_script("arguments[0].click();", button)  # JavaScript click

                # Wait for new offers to load
                time.sleep(random.uniform(2, 5))  # Randomized wait
                WebDriverWait(self.driver, 10).until(
                    lambda d: len(d.find_elements(By.CLASS_NAME, "figure-item")) > previous_count
                )

                # Check if the count of offers has increased
                offer_elements = self.driver.find_elements(By.CLASS_NAME, "figure-item")
                current_count = len(offer_elements)

                if current_count == previous_count:
                    print("No new offers detected. Assuming all offers are loaded.")
                    break
                else:
                    previous_count = current_count
                    print(f"Loaded {current_count} offers so far.")
            except Exception as e:
                print(f"Exiting after encountering an issue: {e}")
                break

        print("Finished loading all available offers.")

    def extract_offers(self):
        """Extract offers data from the loaded page."""
        offers = []
        offer_elements = self.driver.find_elements(By.CLASS_NAME, "figure-item")

        for offer in offer_elements:
            try:
                time.sleep(random.uniform(0.1, 0.3))  # Randomized delay per offer
                title = offer.find_element(By.TAG_NAME, "h2").text
                company = offer.find_element(By.CLASS_NAME, "organization").text
                location = offer.find_element(By.CLASS_NAME, "location").text
                details = offer.find_elements(By.TAG_NAME, "li")
                contract_type = details[0].text if len(details) > 0 else "N/A"
                duration = details[1].text if len(details) > 1 else "N/A"
                views = details[2].text.split()[0] if len(details) > 2 else "0"
                candidates = details[3].text.split()[0] if len(details) > 3 else "0"

                offers.append({
                    "Title": title,
                    "Company": company,
                    "Location": location,
                    "Contract Type": contract_type,
                    "Duration": duration,
                    "Views": views,
                    "Candidates": candidates,
                })
            except Exception as e:
                print(f"Error extracting data for an offer: {e}")
        return offers

    def extract_total_offers(self):
        """Extract the total offers count displayed on the page."""
        try:
            time.sleep(random.uniform(1, 3))  # Randomized delay before accessing total offers count
            total_offers = self.driver.find_element(By.CLASS_NAME, "count").text.split()[0]
            return total_offers
        except Exception as e:
            print(f"Error retrieving total offers count: {e}")
            return "Unknown"

    def scrape(self):
        """Main method to perform the scraping."""
        self.load_all_offers()
        offers = self.extract_offers()
        total_offers = self.extract_total_offers()
        return {
            "total_offers": total_offers,
            "offers": offers
        }

    def close_driver(self):
        """Close the Selenium WebDriver."""
        self.driver.quit()


if __name__ == "__main__":
    url = 'https://mon-vie-via.businessfrance.fr/offres/recherche?query=&specializationsIds=212&specializationsIds=24&missionsTypesIds=1&gerographicZones=4'
    scraper = JobScraper(url)

    try:
        data = scraper.scrape()
        print(f"Total offers found: {data['total_offers']}")
        print(f"Scraped {len(data['offers'])} offers.")
        
        for offer in data['offers']:
            print(f"Title: {offer['Title']}\n"
                  f"Company: {offer['Company']}\n"
                  f"Location: {offer['Location']}\n"
                  f"Contract Type: {offer['Contract Type']}\n"
                  f"Duration: {offer['Duration']}\n"
                  f"Views: {offer['Views']}\n"
                  f"Candidates: {offer['Candidates']}\n"
                  "-----------------------------")
    finally:
        scraper.close_driver()
