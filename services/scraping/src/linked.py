import logging
import os
import re
import warnings
from datetime import datetime
from typing import List, Optional

from services.scraping.src.base_model.job_offer import (
    ContractType,
    JobOfferInput,
    JobSource,
    generate_job_offer_id,
)
from services.scraping.src.base_model.job_scraper_base import JobScraperBase, log_call
from services.scraping.src.linked_url_generate import LinkedinUrlGenerate
from services.storage.src.notion_integration import NotionClient

NUM_JOBS_PER_PAGE = 25



class LinkedInJobScraper(JobScraperBase):
    """LinkedIn Job Scraper using Playwright and Pydantic models."""

    def __init__(
        self,
        notion_client: NotionClient,
        url: str = "https://www.linkedin.com/",
        keyword: str = "",
        location: str = "",
        include_filters: Optional[List[str]] = None,
        exclude_filters: Optional[List[str]] = None,
        debug: bool = False,
        headless: bool = True,
    ):
        super().__init__(
            url=url,
            include_filters=include_filters,
            exclude_filters=exclude_filters,
            debug=debug,
            headless=headless,
            notion_client=notion_client,
            _offers_urls=[],
        )
        self.keyword = keyword
        self.location = location
        self.logger = logging.getLogger("job-tracker.linkedin-scraper")
        # Ensure _offers_urls is always a list
        if self._offers_urls is None:
            self._offers_urls = []
        
        # Cache for iframe reference
        self._iframe_locator = None
        self._use_iframe = False

    def _get_locator(self, selector: str):
        if self._use_iframe and self._iframe_locator:
            return self._iframe_locator.locator(selector)
        else:
            return self.page.locator(selector)

    @log_call()
    async def _detect_dom_structure(self) -> bool:
        if not self.page:
            return False
            
        try:
            iframe_selector = 'iframe[data-testid="interop-iframe"]'
            iframe_locator = self.page.locator(iframe_selector)
            
            if await iframe_locator.count() > 0:
                self._iframe_locator = self.page.frame_locator(iframe_selector)
                
                test_selector = "li[data-occludable-job-id], .jobs-search-box, .job-details-jobs-unified-top-card__container"
                try:
                    await self._iframe_locator.locator(test_selector).first.wait_for(timeout=3000)
                    self._use_iframe = True
                    self.logger.debug("Detected iframe DOM structure")
                    return True
                except:
                    pass
            
            test_selector = "li[data-occludable-job-id], .jobs-search-box, .job-details-jobs-unified-top-card__container"
            try:
                await self.page.locator(test_selector).first.wait_for(timeout=3000)
                self._use_iframe = False
                self._iframe_locator = None
                self.logger.debug("Detected direct page DOM structure")
                return True
            except:
                pass
                
        except Exception as e:
            self.logger.warning(f"Error detecting DOM structure: {e}")
        
        # Default fallback
        self._use_iframe = False
        self._iframe_locator = None
        self.logger.debug("Using default page DOM structure")
        return False

    async def extract_all_offers_url(self) -> None:  # noqa: C901
        """
        Load all offers by applying filters and navigating through pagination.
        """
        if not self.page:
            raise RuntimeError("Page not initialized")

        try:
            await self.page.goto(self.url)
            await self.wait_random(2, 4)
            await self._handle_popups()
            await self.login()

            url_generator = LinkedinUrlGenerate(
                keyword=self.keyword,
                location=self.location,
            )
            await self.page.goto(url_generator.generate_url_link())
            await self.wait_random(2, 4)

            await self._detect_dom_structure()

            total_offers = min(await self._get_total_offers_count(), 500)  # noqa: F84
            self.logger.info(
                f"Total offers found: {total_offers} for keyword '{self.keyword}' and location '{self.location}'"
            )

            total_pages = (total_offers // NUM_JOBS_PER_PAGE) + (1 if total_offers % NUM_JOBS_PER_PAGE else 0)

            # Navigate through pages and collect offer URLs
            for page in range(total_pages):
                try:
                    await self._detect_dom_structure()

                    await self._get_locator(
                        "//li[@data-occludable-job-id]"
                    ).first.wait_for(timeout=10000)

                    
                    await self.wait_random(1, 2)

                    current_page_offers = await self._extract_jobs_urls_and_title_from_current_page()

                    if current_page_offers == 0:
                        self.logger.warning("No offers found on current page, stopping")
                        break

                    if not await self._navigate_to_next_page():
                        self.logger.info("No more pages available")
                        break

                except Exception as e:
                    self.logger.error(f"Error loading page {page}: {e}")
                    break

        except Exception as e:
            raise ValueError(f"Error loading offers: {str(e)}")

        self.logger.info("Finished loading all available offers.")
        self.logger.info(f"Total URLs collected: {len(self._offers_urls)}")

    @log_call()
    async def login(self) -> None:
        if not self.page:
            return
        
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")
        if not email or not password:
            self.logger.error(
                "LinkedIn email or password env vars not set. Skipping login."
            )
            raise RuntimeError(
                "LinkedIn email or password not set in environment variables."
            )
        
        try:
            current_url = self.page.url
            if "/login" not in current_url:
                sign_in_button = self.page.locator('a[data-test-id="home-hero-sign-in-cta"]')
                if await sign_in_button.count() > 0:
                    await sign_in_button.click()
                    await self.wait_random(2, 3)
                else:
                    await self.page.goto("https://www.linkedin.com/login")
                    await self.wait_random(2, 3)
            
            await self.page.wait_for_selector('#username', timeout=10000)
            
            email_input = self.page.locator('#username')
            await email_input.fill(email)
            await self.wait_random(0.5, 1)
            
            password_input = self.page.locator('#password')
            await password_input.fill(password)
            await self.wait_random(0.5, 1)
            
            submit_button = self.page.locator('button.btn__primary--large[data-litms-control-urn="login-submit"][type="submit"]')
            if await submit_button.count() > 0 and await submit_button.is_visible():
                await submit_button.click()
            else:
                await password_input.press("Enter")
            
            await self.wait_random(3, 5)
            
            try:
                await self.page.wait_for_function(
                    """() => {
                        return window.location.pathname !== '/login' || 
                               document.querySelector('.form__label--error:not(.hidden__imp)') !== null
                    }""",
                    timeout=10000
                )
                
                error_elements = self.page.locator('.form__label--error:not(.hidden__imp)')
                if await error_elements.count() > 0:
                    error_text = await error_elements.first.text_content()
                    self.logger.error(f"LinkedIn login failed: {error_text}")
                    raise RuntimeError(f"LinkedIn login failed: {error_text}")
                
                if "/login" in self.page.url:
                    self.logger.warning("Still on login page after submission - login may have failed")
                else:
                    self.logger.info("LinkedIn login successful")
                    
            except Exception as e:
                self.logger.warning(f"Could not verify login status: {e}")
                
            await self.wait_random(4, 5)

        except Exception as e:
            self.logger.error(f"Error during LinkedIn login: {e}")
            raise RuntimeError(f"LinkedIn login failed: {e}")

    async def _get_total_offers_count(self) -> int:
        """Extract total offers count from LinkedIn's results header."""
        if not self.page:
            return 10
        try:
            small_element = self._get_locator('//small').first
            await small_element.wait_for(timeout=5000)
            text = await small_element.text_content()
            if text and text.strip():
                digits_only = re.sub(r"\D", "", text)
                if digits_only:
                    return int(digits_only)
                if "100" in text and "résultats" in text:
                    return 100

        except Exception as e:
            self.logger.warning(f"Error extracting total offers count: {e}")
    
        return 10

    async def _extract_jobs_urls_and_title_from_current_page(self) -> int:  # noqa: C901
        if not self.page:
            return 0

        current_page_offers = 0

        try:
            job_items = self._get_locator("li[data-occludable-job-id]")
            job_count = await job_items.count()

            for i in range(job_count):
                try:
                    job_item = job_items.nth(i)

                    title_link = job_item.locator("a.job-card-container__link").first

                    if await title_link.count() > 0:
                        job_title_element = title_link.locator(
                            "span[aria-hidden='true'] strong"
                        )
                        job_title = await self._safe_get_locator_text(
                            job_title_element, "N/A"
                        )

                        href = await title_link.get_attribute("href")

                        if href and job_title and job_title != "N/A":
                            if self.filter_job_title(job_title):
                                continue

                            if href.startswith("/"):
                                full_url = f"https://www.linkedin.com{href}"
                            else:
                                full_url = href

                            offer_id = generate_job_offer_id(
                                "LinkedIn", job_title, full_url
                            )

                            self._offers_urls.append(
                                {"url": full_url, "id": offer_id, "title": job_title}
                            )
                            current_page_offers += 1

                            self.logger.debug(
                                f"Extracted: {job_title} - {full_url}"
                            )

                except Exception as e:
                    self.logger.debug(f"Error extracting job {i}: {e}")
                    continue

            return current_page_offers

        except Exception as e:
            self.logger.error(f"Error extracting jobs from current page: {e}")
            return 0

    async def _navigate_to_next_page(self) -> bool:
        if not self.page:
            return False

        try:
            next_button = self._get_locator("//button[@aria-label='Voir la page suivante']")
            if await next_button.count() > 0 and await next_button.is_enabled():
                await next_button.scroll_into_view_if_needed()
                await next_button.click()
                await self.wait_random(2, 4)
                return True
        except Exception as e:
            self.logger.info(f"Navigation to next page failed: {e}")
            return False

    @log_call()
    async def parse_offers(self) -> List[JobOfferInput]:  # noqa: C901
        if not self.page:
            raise RuntimeError("Page not initialized")

        offers = []

        for offer in self._offers_urls:
            try:
                await self.page.goto(offer["url"])
                await self._detect_dom_structure()
                await self.wait_random(1, 3)

                pattern = r'<!---->([a-zA-Z0-9_, ]*)<!---->'
                # Title
                try:
                    title_el = self._get_locator("//h1[contains(@class, 't-24 t-bold inline')]").first
                    await title_el.wait_for(timeout=5000)
                    title = (await title_el.inner_html()).strip()
                except Exception as e:
                    self.logger.debug(f"Warning in getting jobTitle: {str(e)[:50]}")
                    title = offer.get("title", "N/A")

                # Company
                try:
                    company_el = self._get_locator("//div[contains(@class, 'job-details-jobs-unified-top-card__company-name')]").first
                    await company_el.wait_for(timeout=5000)
                    company_html = (await company_el.inner_html()).strip()
                    company_match = re.search(pattern, company_html)
                    company = company_match.group(1).strip() if company_match else "N/A"
                except Exception as e:
                    self.logger.debug(f"Warning in getting jobCompany: {str(e)[:50]}")
                    company = "N/A"

                # Location, Posted Date, Applications
                try:
                    desc_el = self._get_locator("//div[contains(@class, 'job-details-jobs-unified-top-card__primary-description-container')]").first
                    await desc_el.wait_for(timeout=5000)
                    desc_html = (await desc_el.inner_html()).strip()
                    desc_matches = re.findall(r'<!---->(.*?)<!---->', desc_html, re.DOTALL)
                    # Remove empty/whitespace-only matches
                    desc_matches = [m.strip() for m in desc_matches if m.strip()]
                    raw_location = desc_matches[0] if len(desc_matches) > 0 else "N/A"
                    location = raw_location.split(",")[0].strip() if "," in raw_location else raw_location.strip()
                    job_posted_date = desc_matches[1] if len(desc_matches) > 2 else ""
                    job_applications = desc_matches[2] if len(desc_matches) > 3 else ""
                except Exception as e:
                    self.logger.debug(f"Warning in getting jobDesc: {str(e)[:50]}")
                    location = "N/A"
                    job_posted_date = ""
                    job_applications = ""

                # Description
                try:
                    desc_full_el = self._get_locator("//div[contains(@class, 'jobs-description-content__text')]").first
                    await desc_full_el.wait_for(timeout=5000)
                    description = (await desc_full_el.inner_text()).strip()
                except Exception as e:
                    self.logger.debug(f"Warning in getting jobDescription: {str(e)[:50]}")
                    description = "N/A"

                # Extract reference/job ID from URL
                reference = self._extract_job_reference(offer["url"])

                offer_input = JobOfferInput(
                    title=title,
                    company=company,
                    location=location,
                    contract_type=ContractType.CDI,
                    reference=reference,
                    job_content_description=description,
                    source=JobSource.LINKEDIN,
                    url=offer["url"],
                    scraped_at=datetime.utcnow(),
                )

                offers.append(offer_input)
                self.logger.debug(
                    f"LinkedIn offer successfully scrapped: {title} at {company} ({location})"
                )

            except Exception as e:
                logging.warning(f"Error extracting data for offer {offer['url']}: {e}")
                self.logger.debug(
                    f"Failed to extract data from URL: {offer['url']}"
                )

        return offers


    def _extract_job_reference(self, url: str) -> str:
        """Extract job ID/reference from LinkedIn URL."""
        try:

            # LinkedIn job URLs follow pattern: /jobs/view/4254887139/...
            job_id_match = re.search(r"/jobs/view/(\d+)", url)
            if job_id_match:
                return job_id_match.group(1)
        except Exception:
            pass
        return "N/A"

    @log_call()
    async def _handle_popups(self) -> None:  # noqa: C901
        """
        Handles LinkedIn popups, specifically cookie consent, by rejecting non-essential cookies.
        """
        if not self.page:
            return

        try:
            # Wait for the global alert container (cookie consent popup)
            popup_container = self.page.locator("#artdeco-global-alert-container")
            if await popup_container.count() > 0:
                # Look for the Reject button inside the popup
                reject_button = popup_container.locator(
                    "button[data-tracking-control-name='ga-cookie.consent.deny.v4'], button[data-control-name='ga-cookie.consent.deny.v4']"
                )
                if await reject_button.count() > 0 and await reject_button.is_visible():
                    await reject_button.click()
                    await self.wait_random(0.5, 1.5)
                    self.logger.info("Rejected LinkedIn cookie consent popup.")
                else:
                    self.logger.info("Reject button not found in cookie consent popup.")
            else:
                self.logger.info("No cookie consent popup detected.")
        except Exception as e:
            self.logger.warning(f"Error handling popups: {e}")


if __name__ == "__main__":

    DATABASE_ID = os.getenv("DATABASE_ID")
    NOTION_API = os.getenv("NOTION_API")
    assert DATABASE_ID, "DATABASE_ID environment variable is not set."
    assert NOTION_API, "NOTION_API environment variable is not set."
    logging.basicConfig(level=logging.DEBUG)
    notion_client = NotionClient(NOTION_API, DATABASE_ID)
    scraper = LinkedInJobScraper(
        keyword="Data engineer",
        location="Paris et périphérie",
        include_filters=["data", "engineer", "ingénieur", "données", "gcp"],
        exclude_filters=["intern", "stage", "apprenti", "business", "management"],
        notion_client=notion_client,
        debug=True,
    )

    job_offers = scraper.scrape()
    logger = logging.getLogger("job-tracker.linkedin-scraper")
    logger.info(f"Scraped {len(job_offers)} job offers from LinkedIn.")
    for offer in job_offers:
        logger.info(f"- {offer.title} at {offer.company} ({offer.location})")
