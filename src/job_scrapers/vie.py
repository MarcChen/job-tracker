from src.job_scrapers.job_scraper_base import JobScraperBase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict, Union
from selenium.common.exceptions import NoSuchElementException
import time
import random
import warnings

class VIEJobScraper(JobScraperBase):
    def __init__(
        self,
        url: str,
        driver: webdriver.Chrome = None,
        debug: bool = False,
        include_filters: List[str] = None,
        exclude_filters: List[str] = None,
    ):
        super().__init__(url, driver=driver)
        self.include_filters = include_filters
        self.exclude_filters = exclude_filters
        self.debug = debug

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
                button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "see-more-btn"))
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                    button,
                )
                time.sleep(random.uniform(1, 2))  # Randomized scroll wait
                self.driver.execute_script(
                    "arguments[0].click();", button
                )  # JavaScript click

                # Wait for new offers to load
                time.sleep(random.uniform(1.5, 2.5))  # Randomized wait
                WebDriverWait(self.driver, 5).until(
                    lambda d: len(
                        d.find_elements(By.CLASS_NAME, "figure-item")
                    )
                    > previous_count
                )

                # Check if the count of offers has increased
                offer_elements = self.driver.find_elements(
                    By.CLASS_NAME, "figure-item"
                )
                current_count = len(offer_elements)

                if current_count == previous_count:
                    print(
                        "No new offers detected. Assuming all offers are loaded."
                    )
                    break
                else:
                    previous_count = current_count
                    print(f"Loaded {current_count} offers so far.")
            except Exception:
                print("Reached last offer")
                break

        print("Finished loading all available offers.")

    def extract_offers(self) -> List[Dict[str, Union[str, int]]]:
        """
        Extract offers data from the loaded page.

        Returns:
            List[Dict[str, Union[str, int]]]: A list of dictionaries containing offer details.
        """
        offers = []
        offer_elements = self.driver.find_elements(
            By.CLASS_NAME, "figure-item"
        )

        for offer in offer_elements:
            offer_data = self._init_offer_dict()
            try:
                time.sleep(
                    random.uniform(0.1, 0.3)
                )  # Randomized delay per offer
                title = offer.find_element(By.TAG_NAME, "h2").text

                # Apply inclusion filter: Skip if none of the include_filters are found.
                if self.include_filters and not any(
                    keyword.lower() in title.lower()
                    for keyword in self.include_filters
                ):
                    print(
                        f"Skipping offer '{title}' (doesn't match include filters)..."
                    )
                    continue

                # Apply exclusion filter: Skip if any of the exclude_filters are found.
                if self.exclude_filters and any(
                    keyword.lower() in title.lower()
                    for keyword in self.exclude_filters
                ):
                    print(
                        f"Skipping offer '{title}' (matches exclude filters)..."
                    )
                    continue
                details = offer.find_elements(By.TAG_NAME, "li")

                offer_data.update(
                    {
                        "Title": title,
                        "Company": offer.find_element(
                            By.CLASS_NAME, "organization"
                        ).text,
                        "Location": offer.find_element(
                            By.CLASS_NAME, "location"
                        ).text,
                        "Contract Type": (
                            details[0].text if len(details) > 0 else "N/A"
                        ),
                        "Duration": (
                            details[1].text if len(details) > 1 else "N/A"
                        ),
                        "Views": (
                            int(details[2].text.split()[0])
                            if len(details) > 2
                            else 0
                        ),
                        "Candidates": (
                            int(details[3].text.split()[0])
                            if len(details) > 3
                            else 0
                        ),
                        "Source": "Business France",
                    }
                )
                offers.append(offer_data)
                print(f"VIE offer extracted: {offer_data}") if self.debug else None
            except Exception as e:
                warnings.warn(f"Error extracting data for an offer: {e}")
        return offers

    def extract_total_offers(self) -> Union[str, int]:
        """
        Extract the total offers count displayed on the page.

        Returns:
            Union[str, int]: The total offers count as an integer, or 'Unknown' if an error occurs.
        """
        try:
            time.sleep(
                random.uniform(1, 3)
            )  # Randomized delay before accessing total offers count
            total_offers = int(
                self.driver.find_element(By.CLASS_NAME, "count").text.split()[
                    0
                ]
            )
            return total_offers
        except Exception as e:
            print(f"Error retrieving total offers count: {e}")
            return "Unknown"