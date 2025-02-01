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
    def __init__(self, url: str, driver: webdriver.Chrome = None, include_filters : List[str] = None, exclude_filters : List[str] = None):
        """
        Initialize the JobScraperBase class.

        Args:
            url (str): The URL of the job listing page to scrape.
        """
        self.url = url
        self.driver = setup_driver() if None else driver

    def _init_offer_dict(self) -> Dict[str, Union[str, int]]:
        """Initialize a standardized offer dictionary with default values."""
        return {
            "Title": "N/A",
            "Company": "N/A",
            "Location": "N/A",
            "Contract Type": "N/A",
            "Duration": "N/A",
            "Views": "N/A",
            "Candidates": "N/A",
            "Source": "N/A",
            "URL": "N/A",
            "Reference": "N/A",
            "Job Category": "N/A",
            "Job Type": "N/A",
            "Schedule Type": "N/A",
            "Description": "N/A"
        }


    def validate_offer(self, offer: dict) -> bool:
        """Ensure required fields are present."""
        required_fields = ["Title", "Company", "Location", "Source"]
        return all(offer[field] != "N/A" for field in required_fields)

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
        raw_offers = self.extract_offers()
        validated_offers = [offer for offer in raw_offers if self.validate_offer(offer)]
        
        return {
            "total_offers": self.extract_total_offers(),
            "offers": validated_offers
        }


class VIEJobScraper(JobScraperBase):
    def __init__(self, url: str, driver: webdriver.Chrome = None, include_filters : List[str] = None, exclude_filters : List[str] = None):
        super().__init__(url, driver=driver)
        self.include_filters = include_filters
        self.exclude_filters = exclude_filters

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
                time.sleep(random.uniform(1.5, 2.5))  # Randomized wait
                WebDriverWait(self.driver, 5).until(
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
                print(f"Reached last offer")
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
            offer_data = self._init_offer_dict()
            try:
                time.sleep(random.uniform(0.1, 0.3))  # Randomized delay per offer
                title = offer.find_element(By.TAG_NAME, "h2").text
                if not any(keyword.lower() in title.strip().lower() for keyword in self.include_filters):
                    print(f"Skipping offer '{title}' ...")
                    continue
                details = offer.find_elements(By.TAG_NAME, "li")

                offer_data.update({
                    "Title": title,
                    "Company": offer.find_element(By.CLASS_NAME, "organization").text,
                    "Location": offer.find_element(By.CLASS_NAME, "location").text,
                    "Contract Type": details[0].text if len(details) > 0 else "N/A",
                    "Duration": details[1].text if len(details) > 1 else "N/A",
                    "Views": int(details[2].text.split()[0]) if len(details) > 2 else 0,
                    "Candidates": int(details[3].text.split()[0]) if len(details) > 3 else 0,
                    "Source": "Business France"
                })
                offers.append(offer_data)
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
    def __init__(self, url: str, keyword: str, contract_type: str, driver: webdriver.Chrome = None, include_filters : List[str] = None, exclude_filters : List[str] = None):

        """
        Initialize the AirFranceJobScraper class.

        Args:
            url (str): The URL of the job listing page to scrape.
            keyword (str): The keyword to search for in job listings.
            contract_type (str): The type of contract to filter job listings.
        """
        super().__init__(url, driver=driver)
        self.keyword = keyword
        self.contract_type = contract_type
        self.offers_url = []
        self.total_offers = 0
        self.include_filters = include_filters
        self.exclude_filters = exclude_filters
        
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

            # Filtering offers 
            if self.keyword == "":
                print("No keyword provided. Skipping keyword filtering.")
            else:
                input_element = self.driver.find_element(By.CSS_SELECTOR, "input[name*='OfferCriteria_Keywords']")
                self.driver.execute_script("arguments[0].value = arguments[1];", input_element, self.keyword)
            
            if self.contract_type == "":
                print("No contract type provided. Skipping contract type filtering.")
            else:
                self.driver.find_element(by=By.ID, value="ctl00_ctl00_moteurRapideOffre_ctl00_EngineCriteriaCollection_Contract").send_keys(self.contract_type)
            
            self.driver.find_element(by=By.ID, value="ctl00_ctl00_moteurRapideOffre_BT_recherche").click()
            print("Offers Filtered.")

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
                    title = title_link.text
                    if not any(keyword.lower() in title.lower() for keyword in self.include_filters) or any(keyword.lower() in title.lower() for keyword in self.exclude_filters):
                        print(f"Skipping offer '{title}' ...")
                        continue
                    self.offers_url.append(title_link.get_attribute("href"))
                print(f"{len(offers)} offers loaded")

                # Attempt to click next page
                try:
                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "ctl00_ctl00_corpsRoot_corps_Pagination_linkSuivPage"))
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
        print(f"Total after filters : {len(self.offers_url)}")


    def extract_offers(self) -> List[Dict[str, Union[str, int]]]:
        """
        Extract offers data from the loaded page.

        Returns:
            List[Dict[str, Union[str, int]]]: A list of dictionaries containing offer details.
        """
        # Implement the logic specific to AirFrance job offers page
        def extract_element(by, value, attribute=None, split_text=None, index=None):
                    try:
                        element = self.driver.find_element(by, value)
                        text = element.get_attribute(attribute) if attribute else element.text
                        if split_text and index is not None:
                            return text.split(split_text)[index].strip()
                        return text.strip()
                    except (NoSuchElementException, IndexError, AttributeError):
                        return "N/A"
                    
        offers = []
        for offer_url in self.offers_url:
            self.driver.get(offer_url)
            time.sleep(random.uniform(1, 3))
            
            # Initialize all fields with default values
            offer_data = self._init_offer_dict()

            try:
                offer_data.update({
                    "Title": extract_element(By.CSS_SELECTOR, "h1.ts-offer-page__title span:first-child"),
                    "Reference": extract_element(By.CLASS_NAME, "ts-offer-page__reference", split_text="Référence", index=1),
                    "Contract Type": extract_element(By.ID, "fldjobdescription_contract"),
                    "Duration": extract_element(By.ID, "fldjobdescription_contractlength"),
                    "Location": extract_element(By.ID, "fldlocation_location_geographicalareacollection").split(",")[0],
                    "Company": extract_element(By.CSS_SELECTOR, "div.ts-offer-page__entity-logo img", attribute="alt", split_text=" - ", index=1),
                    "Job Category": extract_element(By.ID, "fldjobdescription_professionalcategory"),
                    "Schedule Type": extract_element(By.ID, "fldjobdescription_customcodetablevalue3"),
                    "Job Type": extract_element(By.ID, "fldjobdescription_primaryprofile"),
                    "Description": "\n".join([extract_element(By.ID, "fldjobdescription_longtext1"),
                                           extract_element(By.ID, "fldjobdescription_description1")]),
                    "URL": offer_url,
                    "Source": "Air France"
                })
                offers.append(offer_data)
            except Exception as e:
                print(f"Error extracting data for an offer: {e}")
        return offers


    def extract_total_offers(self) -> Union[str, int]:
        """
        Extract the total offers count displayed on the page.

        Returns:
            Union[str, int]: The total offers count as an integer, or 'Unknown' if an error occurs.
        """
        return self.total_offers
    

class AppleJobScraper(JobScraperBase):
    def __init__(self, url: str, driver: webdriver.Chrome = None, include_filters : List[str] = None, exclude_filters : List[str] = None):

        """
        Initialize the AirFranceJobScraper class.

        Args:
            url (str): The URL of the job listing page to scrape.
            keyword (str): The keyword to search for in job listings.
            contract_type (str): The type of contract to filter job listings.
        """
        super().__init__(url, driver=driver)

        self.offers_url = []
        self.total_offers = 0
        self.include_filters = include_filters
        self.exclude_filters = exclude_filters
        
    def load_all_offers(self) -> None:
        """
        Loads all available offers from the specified URL and extracts their URLs.
        This method navigates to the URL specified in the instance, handles the cookie consent popup if present,
        waits for the offers to load, and then extracts the URLs of the offers from the page.
        Raises:
            Exception: If there is an error loading the offers or extracting the URLs.
        Side Effects:
            - Updates the `self.offers_url` list with the URLs of the offers.
            - Updates the `self.total_offers` with the count of the loaded offers.
        """
        try:
            self.driver.get(self.url)
            
            # Handle cookies - adjust selector if different on the actual page
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
                ).click()
                time.sleep(random.uniform(1, 2))
            except Exception:
                pass

            # Wait for offers to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.table--advanced-search__title"))
            )
            self.total_offers = int(WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h2[@id='resultCount']/span[1]"))
            ).text.split()[0])

            # Find all offer rows
            offer_rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody[id^='accordion_']")
            
            loaded_offers = 0 

            while loaded_offers < self.total_offers:
                try :
                    # time.sleep(random.uniform(1, 2))
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "a.table--advanced-search__title"))
                    )
                    offer_rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody[id^='accordion_']")
                    # Extract URLs from title links
                    for row in offer_rows:
                        try:
                            loaded_offers += 1
                            title_link = row.find_element(By.CSS_SELECTOR, "a.table--advanced-search__title")
                            job_title = title_link.text
                            if not any(keyword.lower() in job_title.lower() for keyword in self.include_filters) or any(keyword.lower() in job_title.lower() for keyword in self.exclude_filters):
                                print(f"Skipping offer '{job_title}' ...")
                                continue
                            else : 
                                self.offers_url.append(title_link.get_attribute("href"))
                        except Exception as e:
                            print(f"Error extracting link from row: {str(e)}")

                    print(f"Loaded {loaded_offers} / {self.total_offers}")

                    # Scroll to the last offer row
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", offer_rows[-1])

                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "li.pagination__next a:not([aria-disabled='true'])"))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", next_button)
                    self.driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(random.uniform(1.5, 2.5))

                except Exception as e:
                    print(f"Reached last offer")
                    break
                

        except Exception as e:
            print(f"Error loading offers: {str(e)}")
            raise

        print(f"TOTAL OFFERS : {len(self.offers_url)}")
        print("Finished loading all available offers.")


    def extract_offers(self) -> List[Dict[str, Union[str, int]]]:
        """
        Extract offers data from the loaded page.

        Returns:
            List[Dict[str, Union[str, int]]]: A list of dictionaries containing offer details.
        """
        def extract_element(by, value, attribute=None, split_text=None, index=None):
                    try:
                        element = self.driver.find_element(by, value)
                        text = element.get_attribute(attribute) if attribute else element.text
                        if split_text and index is not None:
                            return text.split(split_text)[index].strip()
                        return text.strip()
                    except (NoSuchElementException, IndexError, AttributeError):
                        return "N/A"
                    
        offers = []
        for offer_url in self.offers_url:
            self.driver.get(offer_url)
            time.sleep(random.uniform(1, 3))
            
            # Initialize all fields with default values
            offer_data = self._init_offer_dict()

            try:
                offer_data.update({
                    "Title": extract_element(By.ID, "jdPostingTitle"),
                    "Reference": extract_element(By.ID, "jobNumber"),
                    "Location": extract_element(By.ID, "job-location-name", split_text=",", index=0), # Retrieve City 
                    "Schedule Type": extract_element(By.ID, "jobWeeklyHours"),
                    "Job Type": extract_element(By.ID, "job-team-name"),
                    "Description": "\n".join([
                        extract_element(By.ID, "jd-job-summary"),
                        extract_element(By.ID, "jd-description"),
                        "Minimum Qualification\n" + extract_element(By.ID, "jd-minimum-qualifications"),
                        "Preferred Qualification\n" + extract_element(By.ID, "jd-preferred-qualifications"),
                    ]),
                    "URL": offer_url,
                    "Source": "Apple"
                })
                offers.append(offer_data)
            except Exception as e:
                print(f"Error extracting data for an offer: {e}")
        return offers


    def extract_total_offers(self) -> int:
        """
        Extract the total offers count displayed on the page.

        Returns:
            int: The total offers count as an integer, or 'Unknown' if an error occurs.
        """
        return self.total_offers
    

def setup_driver(debug : bool = False) -> webdriver.Chrome:
        """
        Set up the Selenium WebDriver with necessary options.

        Returns:
            webdriver.Chrome: Configured Selenium WebDriver instance.
        """
        if not debug:
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