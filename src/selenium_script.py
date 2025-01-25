from ctypes import c_ssize_t
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import random
from typing import List, Dict, Union
import logging

class JobScraperBase:
    def __init__(self, url: str, debug: bool = True):
        """
        Initialize the JobScraperBase class.

        Args:
            url (str): The URL of the job listing page to scrape.
        """
        self.url = url
        self.debug = debug
        self.driver = self._setup_driver()

    def _setup_driver(self) -> webdriver.Chrome:
        """
        Set up the Selenium WebDriver with necessary options.

        Returns:
            webdriver.Chrome: Configured Selenium WebDriver instance.
        """
        if not self.debug:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--start-maximized')  # Open in full screen
            chrome_options.binary_location = '/usr/bin/chromium'
            service = Service('/usr/bin/chromedriver')

            return webdriver.Chrome(service=service, options=chrome_options)
        else:
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')  # Open in full screen

            # Use Remote WebDriver to connect to the Selenium container
            driver = webdriver.Remote(
            command_executor='http://localhost:4444/wd/hub',
            options=options
            )
            return driver

    def load_all_offers(self) -> None:
        """
        Load all offers by repeatedly clicking 'Voir Plus d'Offres' with added randomness.
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    def extract_offers(self) -> List[Dict[str, Union[str, int]]]:
        """
        Extract offers data from the loaded page.

        Returns:
            List[Dict[str, Union[str, int]]]: A list of dictionaries containing offer details.
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    def extract_total_offers(self) -> Union[str, int]:
        """
        Extract the total offers count displayed on the page.

        Returns:
            Union[str, int]: The total offers count as an integer, or 'Unknown' if an error occurs.
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    def scrape(self) -> Dict[str, Union[str, List[Dict[str, Union[str, int]]]]]:
        """
        Main method to perform the scraping.

        Returns:
            Dict[str, Union[str, List[Dict[str, Union[str, int]]]]]: A dictionary containing the total offers count and offers data.
        """
        self.load_all_offers()
        offers = self.extract_offers()
        total_offers = self.extract_total_offers()
        return {
            "total_offers": total_offers,
            "offers": offers
        }

    def close_driver(self) -> None:
        """
        Close the Selenium WebDriver.
        """
        self.driver.quit()

class VIEJobScraper(JobScraperBase):
    def load_all_offers(self) -> None:
        """
        Load all offers by repeatedly clicking 'Voir Plus d'Offres' with added randomness.
        """
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

    def extract_offers(self) -> List[Dict[str, Union[str, int]]]:
        """
        Extract offers data from the loaded page.

        Returns:
            List[Dict[str, Union[str, int]]]: A list of dictionaries containing offer details.
        """
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
                views = int(details[2].text.split()[0]) if len(details) > 2 else 0
                candidates = int(details[3].text.split()[0]) if len(details) > 3 else 0

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

    def extract_total_offers(self) -> Union[str, int]:
        """
        Extract the total offers count displayed on the page.

        Returns:
            Union[str, int]: The total offers count as an integer, or 'Unknown' if an error occurs.
        """
        try:
            time.sleep(random.uniform(1, 3))  # Randomized delay before accessing total offers count
            total_offers = int(self.driver.find_element(By.CLASS_NAME, "count").text.split()[0])
            return total_offers
        except Exception as e:
            print(f"Error retrieving total offers count: {e}")
            return "Unknown"

class AirFranceJobScraper(JobScraperBase):
    def __init__(self, url: str, keyword: str, contract_type: str):
        """
        Initialize the AirFranceJobScraper class.

        Args:
            url (str): The URL of the job listing page to scrape.
            keyword (str): The keyword to search for in job listings.
            contract_type (str): The type of contract to filter job listings.
        """
        super().__init__(url)
        # Geting the page
        self.keyword = keyword
        self.contract_type = contract_type
        self.offers_url = []
        self.total_offers = 0
        
        time.sleep(random.uniform(1, 4))  # Randomized initial wait
    def load_all_offers(self) -> None:
        try:
            self.driver.get(self.url)
            # Handle cookies
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
                ).click()
                time.sleep(random.uniform(1, 2))
                self.driver.navigate().refresh()
            except Exception:
                pass

            # Enter keyword
            print("Waiting for keyword input field to be clickable.")
            input_element = self.driver.find_element(By.CSS_SELECTOR, "input[name*='OfferCriteria_Keywords']")
            self.driver.execute_script("arguments[0].value = arguments[1];", input_element, self.keyword)


            # self.driver.find_element(by=By.ID, value="ctl00_ctl00_moteurRapideOffre_ctl00_OfferCriteria_Keywords").send_keys(self.keyword)


            # # Select contract type
            print("Waiting for contract select element to be present.")
            # # contract_select_element = WebDriverWait(self.driver, 20).until(
            # #     EC.presence_of_element_located((By.ID, "ctl00_ctl00_moteurRapideOffre_ctl00_EngineCriteriaCollection_Contract"))
            # # )
            # # print("Contract select element is present.")
            # # contract_select = Select(contract_select_element)
            # # contract_select.select_by_visible_text(self.contract_type)
            self.driver.find_element(by=By.ID, value="ctl00_ctl00_moteurRapideOffre_ctl00_EngineCriteriaCollection_Contract").send_keys(self.contract_type)

            # # Click search button
            # print("Waiting for search button to be clickable.")
            # # search_button = WebDriverWait(self.driver, 20).until(
            # #     EC.element_to_be_clickable((By.ID, "ctl00_ctl00_moteurRapideOffre_BT_recherche"))
            # # )
            # # print("Search button is clickable.")
            # # search_button.click()
            self.driver.find_element(by=By.ID, value="ctl00_ctl00_moteurRapideOffre_BT_recherche").click()

            # # Wait for results to load and get total offers
            print("Waiting for results to load.")
            count_element = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "ctl00_ctl00_corpsRoot_corps_PaginationLower_TotalOffers"))
            )
            self.total_offers = int(count_element.text.split()[0])

            while True:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "ts-offer-list-item"))
                )
                offers = self.driver.find_elements(By.CLASS_NAME, "ts-offer-list-item")
                for offer in offers:
                    title_link = offer.find_element(By.CLASS_NAME, "ts-offer-list-item__title-link")
                    self.offers_url.append(title_link.get_attribute("href"))
                    print(f"Added offer URL: {title_link.get_attribute('href')}")

                # Attempt to click next page
                try:
                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a[title='Page suivante de résultats d'offres']"))
                    )
                    next_button.click()
                    time.sleep(random.uniform(1, 3))
                    # Wait for new page to load
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "ts-offer-list-item"))
                    )
                except Exception:
                    print("Reached last page or could not find next button")
                    break

        except Exception as e:
            print(f"Error loading offers: {str(e)}")
            raise  # Re-raise exception to see full traceback

        print("Finished loading all available offers.")


    def extract_offers(self) -> List[Dict[str, Union[str, int]]]:
        """
        Extract offers data from the loaded page.

        Returns:
            List[Dict[str, Union[str, int]]]: A list of dictionaries containing offer details.
        """
        # Implement the logic specific to AirFrance job offers page
        pass
