import random
import time
from typing import Dict, List, Union

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.job_scrapers.job_scraper_base import JobScraperBase


class AppleJobScraper(JobScraperBase):
    def __init__(
        self,
        url: str,
        driver: webdriver.Chrome = None,
        debug: bool = False,
        include_filters: List[str] = [],
        exclude_filters: List[str] = [],
    ):
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
        self.debug = debug

    def load_all_offers(self) -> None:  # noqa: C901
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
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "a.table--advanced-search__title")
                )
            )
            self.total_offers = int(
                WebDriverWait(self.driver, 10)
                .until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//h2[@id='resultCount']/span[1]")
                    )
                )
                .text.split()[0]
            )

            # Find all offer rows
            offer_rows = self.driver.find_elements(
                By.CSS_SELECTOR, "tbody[id^='accordion_']"
            )

            loaded_offers = 0

            while loaded_offers < self.total_offers:
                try:
                    # time.sleep(random.uniform(1, 2))
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located(
                            (
                                By.CSS_SELECTOR,
                                "a.table--advanced-search__title",
                            )
                        )
                    )
                    offer_rows = self.driver.find_elements(
                        By.CSS_SELECTOR, "tbody[id^='accordion_']"
                    )
                    # Extract URLs from title links
                    for row in offer_rows:
                        try:
                            loaded_offers += 1
                            title_link = row.find_element(
                                By.CSS_SELECTOR,
                                "a.table--advanced-search__title",
                            )
                            job_title = title_link.text
                            if not any(
                                keyword.lower() in job_title.lower()
                                for keyword in self.include_filters
                            ) or any(
                                keyword.lower() in job_title.lower()
                                for keyword in self.exclude_filters
                            ):
                                print(f"Skipping offer '{job_title}' ...")
                                continue
                            else:
                                self.offers_url.append(title_link.get_attribute("href"))
                        except Exception as e:
                            print(f"Error extracting link from row: {str(e)}")

                    print(f"Loaded {loaded_offers} / {self.total_offers}")

                    # Scroll to the last offer row
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                        offer_rows[-1],
                    )

                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(
                            (
                                By.CSS_SELECTOR,
                                "li.pagination__next a:not([aria-disabled='true'])",
                            )
                        )
                    )
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                        next_button,
                    )
                    self.driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(random.uniform(1.5, 2.5))

                except Exception:
                    print("Reached last offer")
                    break

        except Exception as e:
            raise ValueError(f"Error loading offers: {e}")

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
                offer_data.update(
                    {
                        "Title": extract_element(By.ID, "jdPostingTitle"),
                        "Reference": extract_element(By.ID, "jobNumber"),
                        "Location": extract_element(
                            By.ID, "job-location-name", split_text=",", index=0
                        ),  # Retrieve City
                        "Schedule Type": extract_element(By.ID, "jobWeeklyHours"),
                        "Job Type": extract_element(By.ID, "job-team-name"),
                        "Description": "\n".join(
                            [
                                # extract_element(By.ID, "jd-job-summary"), Removed cuz description is too long
                                "Job Description\n"
                                + extract_element(By.ID, "jd-description")
                                + "\n",
                                "Minimum Qualification\n"
                                + extract_element(By.ID, "jd-minimum-qualifications")
                                + "\n",
                                "Preferred Qualification\n"
                                + extract_element(By.ID, "jd-preferred-qualifications"),
                            ]
                        ),
                        "URL": offer_url,
                        "Contract Type": "CDI",
                        "Company": "Apple",
                        "Source": "Apple",
                    }
                )
                offers.append(offer_data)
                if self.debug:
                    from rich import print

                    print(offer_data)
            except Exception as e:
                raise ValueError(f"Error extracting data for an offer: {e}")
        return offers

    def extract_total_offers(self) -> int:
        """
        Extract the total offers count displayed on the page.

        Returns:
            int: The total offers count as an integer, or 'Unknown' if an error occurs.
        """
        return self.total_offers
