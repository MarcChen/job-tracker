import random
import time
from typing import Dict, List, Union

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.job_scrapers.job_scraper_base import JobScraperBase


class WelcomeToTheJungleJobScraper(JobScraperBase):
    def __init__(
        self,
        url: str,
        driver: webdriver.Chrome = None,
        debug: bool = False,
        include_filters: List[str] = [],
        exclude_filters: List[str] = [],
    ):
        """
        Initialize the WelcomeToTheJungleJobScraper.

        Args:
            url (str): The URL of the Welcome to the Jungle jobs listing page.
            driver (webdriver.Chrome): A Selenium driver instance.
            debug (bool): Whether to print debug information.
            include_filters (List[str]): Keywords to include.
            exclude_filters (List[str]): Keywords to exclude.
        """
        super().__init__(url, driver=driver)
        self.offers_url = []
        self.total_offers = 0
        self.include_filters = include_filters
        self.exclude_filters = exclude_filters
        self.debug = debug

    def load_all_offers(self) -> None:
        """
        Loads all available offers from the Welcome to the Jungle listing page.
        The method navigates to the URL, waits for the job cards to appear,
        extracts the offer URLs from each job card, and iterates through the
        pagination using the "next" button.
        """
        try:
            self.driver.get(self.url)

            for selector in [
                "#axeptio_btn_dismiss",
                "#axeptio_btn_configure",
                "#axeptio_btn_acceptAll",
            ]:
                try:
                    WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    ).click()
                    time.sleep(random.uniform(1, 2))
                    break
                except Exception:
                    continue
    
            self.total_offers = int(
                WebDriverWait(self.driver, 10)
                .until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div[data-testid='jobs-search-results-count']")
                    )
                )
                .text
            )
            print(f"Total offers found: {self.total_offers}")

            # Find all offer rows (adjusted to list items inside the offers container)
            offer_rows = self.driver.find_elements(
                By.CSS_SELECTOR, "li[data-testid='search-results-list-item-wrapper']"
            )
            print(f"Found {len(offer_rows)} offer rows")

            loaded_offers = 0
            for row in offer_rows:
                try:
                    title_link = row.find_element(By.CSS_SELECTOR, "a")
                    job_title = title_link.text
                    if self.include_filters and not any(
                        keyword.lower() in job_title.lower() for keyword in self.include_filters
                    ):
                        print(f"Skipping offer '{job_title}' (does not match include filters)")
                        continue
                    if self.exclude_filters and any(
                        keyword.lower() in job_title.lower() for keyword in self.exclude_filters
                    ):
                        print(f"Skipping offer '{job_title}' (matches exclude filters)")
                        continue
                    self.offers_url.append(title_link.get_attribute("href"))
                    loaded_offers += 1
                except Exception as e:
                    print(f"Error processing row: {e}")
            print(f"Loaded {loaded_offers} offers")
        except Exception as e:
            raise ValueError(f"Error loading offers: {e}")

        # print(f"TOTAL OFFERS : {len(self.offers_url)}")
        # print("Finished loading all available offers.")

    def extract_offers(self) -> List[Dict[str, Union[str, int]]]:
        """
        Extracts detailed data from each job offer page.
        Note: The CSS selectors below are assumed for the job detail pages. They may
        need to be updated after inspecting a typical job detail page on Welcome to the Jungle.

        Returns:
            List[Dict[str, Union[str, int]]]: A list of dictionaries with job details.
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
            offer_data = self._init_offer_dict()  # Initialize with defaults

            try:
                offer_data.update({
                    "Title": extract_element(By.CSS_SELECTOR, "h1[data-testid='job-detail-title']"),
                    "Reference": extract_element(By.CSS_SELECTOR, "span[data-testid='job-detail-reference']"),
                    "Location": extract_element(By.CSS_SELECTOR, "p[data-testid='job-detail-location']"),
                    "Schedule Type": extract_element(By.CSS_SELECTOR, "div[data-testid='job-detail-schedule']"),
                    "Job Type": extract_element(By.CSS_SELECTOR, "div[data-testid='job-detail-type']"),
                    "Description": extract_element(By.CSS_SELECTOR, "div[data-testid='job-detail-description']"),
                    "URL": offer_url,
                    "Contract Type": extract_element(By.CSS_SELECTOR, "div[data-testid='job-detail-contract']"),
                    "Company": "Welcome to the Jungle",
                    "Source": "Welcome to the Jungle",
                })
                offers.append(offer_data)
                if self.debug:
                    print(f"WTJ offer extracted: {offer_data}")
            except Exception as e:
                raise ValueError(f"Error extracting data for an offer: {e}")

        return offers

    def extract_total_offers(self) -> int:
        """
        Returns the total number of offers loaded.
        """
        return self.total_offers
