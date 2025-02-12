import random
import time
import warnings
from typing import Dict, List, Union

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.job_scrapers.job_scraper_base import JobScraperBase


class AirFranceJobScraper(JobScraperBase):
    def __init__(
        self,
        url: str,
        keyword: str,
        contract_type: str,
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
        self.keyword = keyword
        self.contract_type = contract_type
        self.offers_url = []
        self.total_offers = 0
        self.include_filters = include_filters
        self.exclude_filters = exclude_filters
        self.debug = debug

    def load_all_offers(self) -> None:  # noqa: C901
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
                input_element = self.driver.find_element(
                    By.CSS_SELECTOR, "input[name*='OfferCriteria_Keywords']"
                )
                self.driver.execute_script(
                    "arguments[0].value = arguments[1];",
                    input_element,
                    self.keyword,
                )

            if self.contract_type == "":
                print("No contract type provided. Skipping contract type filtering.")
            else:
                self.driver.find_element(
                    by=By.ID,
                    value="ctl00_ctl00_moteurRapideOffre_ctl00_EngineCriteriaCollection_Contract",
                ).send_keys(self.contract_type)

            self.driver.find_element(
                by=By.ID, value="ctl00_ctl00_moteurRapideOffre_BT_recherche"
            ).click()
            print("Offers Filtered.")

            count_element = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (
                        By.ID,
                        "ctl00_ctl00_corpsRoot_corps_PaginationLower_TotalOffers",
                    )
                )
            )
            self.total_offers = int(count_element.text.split()[0])

            while True:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "ts-offer-list-item")
                    )
                )
                offers = self.driver.find_elements(By.CLASS_NAME, "ts-offer-list-item")
                for offer in offers:
                    title_link = offer.find_element(
                        By.CLASS_NAME, "ts-offer-list-item__title-link"
                    )
                    title = title_link.text
                    if not any(
                        keyword.lower() in title.lower()
                        for keyword in self.include_filters
                    ) or any(
                        keyword.lower() in title.lower()
                        for keyword in self.exclude_filters
                    ):
                        print(f"Skipping offer '{title}' ...")
                        continue
                    self.offers_url.append(title_link.get_attribute("href"))
                print(f"{len(offers)} offers loaded")

                # Attempt to click next page
                try:
                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(
                            (
                                By.ID,
                                "ctl00_ctl00_corpsRoot_corps_Pagination_linkSuivPage",
                            )
                        )
                    )
                    next_button.click()
                    time.sleep(random.uniform(1, 3))
                    # Wait for new page to load
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, "ts-offer-list-item")
                        )
                    )
                except Exception:
                    print("Reached last page or could not find next button")
                    break

        except Exception as e:
            raise ValueError(f"Error loading offers: {str(e)}")

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
                warnings.warn(f"Error extracting element: {value}")
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
                        "Title": extract_element(
                            By.CSS_SELECTOR,
                            "h1.ts-offer-page__title span:first-child",
                        ),
                        "Reference": extract_element(
                            By.CLASS_NAME,
                            "ts-offer-page__reference",
                            split_text="Référence",
                            index=1,
                        ),
                        "Contract Type": extract_element(
                            By.ID, "fldjobdescription_contract"
                        ),
                        "Duration": extract_element(
                            By.ID, "fldjobdescription_contractlength"
                        ),
                        "Location": extract_element(
                            By.ID,
                            "fldlocation_location_geographicalareacollection",
                        ).split(",")[0],
                        "Company": extract_element(
                            By.CSS_SELECTOR,
                            "div.ts-offer-page__entity-logo img",
                            attribute="alt",
                            split_text=" - ",
                            index=1,
                        ),
                        "Job Category": extract_element(
                            By.ID, "fldjobdescription_professionalcategory"
                        ),
                        "Schedule Type": extract_element(
                            By.ID, "fldjobdescription_customcodetablevalue3"
                        ),
                        "Job Type": extract_element(
                            By.ID, "fldjobdescription_primaryprofile"
                        ),
                        "Description": "\n".join(
                            [
                                extract_element(By.ID, "fldjobdescription_longtext1"),
                                extract_element(
                                    By.ID, "fldjobdescription_description1"
                                ),
                            ]
                        ),
                        "URL": offer_url,
                        "Source": "Air France",
                    }
                )
                offers.append(offer_data)
                if self.debug:
                    from rich import print
                    print(offer_data)
            except Exception as e:
                raise ValueError(f"Error extracting data for an offer: {e}")
        return offers

    def extract_total_offers(self) -> Union[str, int]:
        """
        Extract the total offers count displayed on the page.

        Returns:
            Union[str, int]: The total offers count as an integer, or 'Unknown' if an error occurs.
        """
        return self.total_offers
