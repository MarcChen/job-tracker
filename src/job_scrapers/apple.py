import random
import re
import time
from typing import Dict, List, Union

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.job_scrapers.job_scraper_base import JobScraperBase
from src.notion_integration import NotionClient


class AppleJobScraper(JobScraperBase):
    def __init__(
        self,
        url: str,
        driver: webdriver.Chrome = None,
        debug: bool = False,
        include_filters: List[str] = [],
        exclude_filters: List[str] = [],
        notion_client: NotionClient = None,
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
        self.notion_client = notion_client

    def load_all_offers(self) -> None:  # noqa: C901
        """
        Loads all available offers from the specified URL and extracts their URLs.
        """
        try:
            self.driver.get(self.url)

            # Handle cookies
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
                ).click()
                time.sleep(random.uniform(1, 2))
            except Exception:
                pass

            try:
                total_offers_text = (
                    WebDriverWait(self.driver, 15)
                    .until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, "t-eyebrow-reduced")
                        )
                    )
                    .text
                )
                print(f"Total offers text found: {total_offers_text}")

                match = re.search(r"(\d+)", total_offers_text)
                if match:
                    self.total_offers = int(match.group(1))
                else:
                    raise ValueError(
                        f"Could not extract total offers from text: {total_offers_text}"
                    )
            except Exception as e:
                raise ValueError(f"Could not determine total offers: {e}")

            loaded_offers = 0

            while loaded_offers < self.total_offers:
                try:
                    # Wait until at least one offer link is present
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located(
                            # The new link class from your snippet
                            (
                                By.CSS_SELECTOR,
                                "a.link-inline.t-intro.word-wrap-break-word",
                            )
                        )
                    )

                    # Each job is now in <li data-core-accordion-item="">
                    offer_rows = self.driver.find_elements(
                        By.CSS_SELECTOR, "li[data-core-accordion-item]"
                    )

                    for row in offer_rows:
                        try:
                            title_link = row.find_element(
                                By.CLASS_NAME,
                                "link-inline.t-intro.word-wrap-break-word",
                            )
                            job_title = title_link.text
                            loaded_offers += 1

                            if self.should_skip_offer(job_title):
                                continue

                            elif self.notion_client.offer_exists(
                                title=job_title, source="Apple", company="Apple"
                            ):
                                print(
                                    f"Skipping offer '{job_title}' (already exists in Notion)..."
                                )
                                continue
                            else:
                                self.offers_url.append(title_link.get_attribute("href"))

                        except Exception as e:
                            print(f"Error extracting link from row: {str(e)}")

                    print(f"Loaded {loaded_offers} / {self.total_offers}")

                    # Scroll to last job row
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        offer_rows[-1],
                    )
                    time.sleep(random.uniform(1, 2))

                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(
                            (
                                By.CSS_SELECTOR,
                                "button.icon.icon-chevronend:not([disabled])",
                            )
                        )
                    )
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        next_button,
                    )
                    self.driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(random.uniform(1.5, 2.5))

                except TimeoutException:
                    print("No more 'Next page' button found or last page reached.")
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
                        "Title": extract_element(By.ID, "jobdetails-postingtitle"),
                        "Reference": extract_element(By.ID, "jobdetails-jobnumber"),
                        "Location": extract_element(By.ID, "jobdetails-joblocation"),
                        "Schedule Type": extract_element(
                            By.ID, "jobdetails-weeklyhours"
                        ),
                        "Job Type": extract_element(By.ID, "jobdetails-teamname"),
                        "Description": "\n".join(
                            [
                                extract_element(
                                    By.ID,
                                    "jobdetails-jobdetails-jobsummary-content-row",
                                ),
                                extract_element(
                                    By.ID,
                                    "jobdetails-jobdetails-jobdescription-content-row",
                                ),
                                extract_element(
                                    By.ID,
                                    "jobdetails-jobdetails-minimumqualifications-content-row",
                                ),
                                extract_element(
                                    By.ID,
                                    "jobdetails-jobdetails-preferredqualifications-content-row",
                                ),
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
