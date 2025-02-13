import random
import time
from typing import Dict, List, Union

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.job_scrapers.job_scraper_base import JobScraperBase
from src.notion_integration import NotionClient


class WelcomeToTheJungleJobScraper(JobScraperBase):
    def __init__(
        self,
        url: str,
        driver: webdriver.Chrome = None,
        debug: bool = False,
        include_filters: List[str] = [],
        exclude_filters: List[str] = [],
        keyword: str = "",
        location: str = "",
        notion_client: NotionClient = None,
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
        self.keyword = keyword
        self.location = location
        self.notion_client = notion_client

    def load_all_offers(self) -> None:  # noqa: C901
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

            try:
                french_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            "button[data-testid='country-banner-stay-button']",
                        )
                    )
                )
                french_btn.click()
                time.sleep(random.uniform(1, 2))
            except Exception:
                pass

            location_input = self.driver.find_element(
                By.CSS_SELECTOR, "#search-location-field"
            )
            clear_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[data-testid='clear-dropdown-search']")
                )
            )
            clear_button.click()
            location_input.send_keys(self.location)
            time.sleep(random.uniform(1, 1.5))
            location_input.send_keys(Keys.ENTER)
            time.sleep(random.uniform(1, 2))

            # Add filters by entering keyword, location, and selecting job type
            search_input = self.driver.find_element(
                By.CSS_SELECTOR, "#search-query-field"
            )
            search_input.clear()
            search_input.send_keys(self.keyword)
            search_input.send_keys(Keys.ENTER)
            time.sleep(random.uniform(1, 2))

            self.total_offers = int(
                WebDriverWait(self.driver, 10)
                .until(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            "div[data-testid='jobs-search-results-count']",
                        )
                    )
                )
                .text
            )
            print(f"Total offers found: {self.total_offers}")

            loaded_offers = 0
            while loaded_offers < self.total_offers:
                offer_rows = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "li[data-testid='search-results-list-item-wrapper']",
                )
                for row in offer_rows:
                    try:
                        loaded_offers += 1
                        job_link = row.find_element(
                            By.CSS_SELECTOR, "a[mode='grid'].sc-dnvZjJ.dhlcJw"
                        )
                        job_title = row.find_element(
                            By.CSS_SELECTOR, "a h4 div[role='mark']"
                        ).text
                        if self.should_skip_offer(job_title):
                            continue
                        elif self.notion_client.offer_exists(
                            title=job_title, source="Welcome to the Jungle"
                        ):
                            print(
                                f"Skipping offer '{job_title}' (already exists in Notion database)..."
                            )
                            continue
                        self.offers_url.append(job_link.get_attribute("href"))
                    except Exception as e:
                        print(f"Error processing row: {e}")

                print(f"Loaded {loaded_offers} offers")

                if loaded_offers >= self.total_offers:
                    break

                try:
                    # Locate the pagination container and its last <li> element (which contains the "next" button)
                    pagination = self.driver.find_element(
                        By.CSS_SELECTOR, "ul.sc-mkoLC.cDMQpP"
                    )
                    next_button_li = pagination.find_elements(By.TAG_NAME, "li")[-1]
                    # Scroll the last <li> into view
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                        next_button_li,
                    )
                    # Wait for the "next" button to be clickable and click it
                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "ul.sc-mkoLC.cDMQpP li:last-child a")
                        )
                    )
                    time.sleep(random.uniform(1, 2))
                    next_button.click()
                    time.sleep(random.uniform(1, 3))
                except Exception:
                    print("Reached last offer")
                    break

        except Exception as e:
            raise ValueError(f"Error loading offers: {e}")

        print(f"TOTAL OFFERS : {len(self.offers_url)}")
        print("Finished loading all available offers.")

    def extract_offers(self) -> List[Dict[str, Union[str, int]]]:  # noqa: C901
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
        self.total_offers = len(self.offers_url)
        for offer_url in self.offers_url:
            self.driver.get(offer_url)
            time.sleep(random.uniform(1, 3))
            offer_data = self._init_offer_dict()  # Initialize with defaults

            try:
                desc_perks = extract_element(
                    By.CSS_SELECTOR, "div[data-testid='perks_and_benefits_block']"
                )
                desc_post = extract_element(
                    By.CSS_SELECTOR, "div[data-testid='job-section-description']"
                )
                remote_work = extract_element(
                    By.XPATH,
                    "//div[@variant='default' and @w='fit-content' and contains(@class, 'sc-eXsaLi') and contains(@class, 'kvWjSS') and .//i[@name='remote']]//span",
                )
                lines = []
                if remote_work != "Télétravail non renseigné":
                    lines.append(f"Remote : {remote_work}")
                if desc_perks and desc_perks != "N/A":
                    lines.append(f" Benefits ! {desc_perks}")
                if desc_post and desc_post != "N/A":
                    lines.append(desc_post)
                combined_desc = "\n".join(lines).strip()
                offer_data.update(
                    {
                        "Title": extract_element(
                            By.CSS_SELECTOR, "h2.sc-fThUAz.fZjqKw.wui-text"
                        ),
                        "Location": extract_element(
                            By.CSS_SELECTOR, "div.sc-eXsaLi.kvWjSS span.sc-mkoLC.cfCdii"
                        ),
                        "Salary": extract_element(
                            By.CSS_SELECTOR,
                            "div.sc-eXsaLi.kvWjSS",
                            split_text="Salaire :",
                            index=1,
                        ),
                        "Experience Level": extract_element(
                            By.XPATH,
                            "//div[@variant='default' and @w='fit-content' and contains(@class, 'sc-eXsaLi') and contains(@class, 'kvWjSS') and .//i[@name='suitcase']]",
                            split_text="Expérience :",
                            index=1,
                        ),
                        "Schedule Type": extract_element(
                            By.CSS_SELECTOR, "div[data-testid='job-detail-schedule']"
                        ),
                        "Job Type": extract_element(
                            By.CSS_SELECTOR, "div[data-testid='job-detail-type']"
                        ),
                        "Description": combined_desc,
                        "URL": offer_url,
                        "Contract Type": extract_element(
                            By.CSS_SELECTOR,
                            "div[variant='default'][w='fit-content'].sc-eXsaLi.kvWjSS",
                        ),
                        "Company": extract_element(
                            By.CSS_SELECTOR,
                            "div.sc-bXCLTC.dPVkkc a.sc-fremEr.gbSfGo span",
                        ),
                        "Source": "Welcome to the Jungle",
                    }
                )
                offers.append(offer_data)
                if self.debug:
                    from rich import print

                    print(offer_data)
            except Exception as e:
                raise ValueError(f"Error extracting data for an offer: {e}")

        return offers
