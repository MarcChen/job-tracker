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

MAX_JOBS_TO_FETCH = 300
OFFER_PER_CLICK = 10


class LinkedInJobScraper(JobScraperBase):
    def __init__(
        self,
        notion_client: NotionClient,
        url: str = "https://www.linkedin.com/jobs",
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
                    await self._iframe_locator.locator(test_selector).first.wait_for(
                        timeout=3000
                    )
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
        return False

    async def extract_all_offers_url(self) -> None:  # noqa: C901
        """
        Load all offers by applying filters and navigating through pagination.
        """
        if not self.page:
            raise RuntimeError("Page not initialized")

        try:
            url_generator = LinkedinUrlGenerate(
                keyword=self.keyword,
                location=self.location,
            )
            await self.page.goto(url_generator.generate_url_link())
            await self.wait_random(2, 4)
            await self._handle_popups()
            await self.accept_cookies()

            await self._detect_dom_structure()

            total_offers = min(
                await self._get_total_offers_count(), MAX_JOBS_TO_FETCH
            )  # noqa: F84
            self.logger.info(
                f"Total offers found: {total_offers} for keyword '{self.keyword}' and location '{self.location}'"
            )

            # Load all offers
            loaded_offers = 0
            while loaded_offers < total_offers:
                try:
                    await self._detect_dom_structure()
                    await self._get_locator("ul.jobs-search__results-list").wait_for(
                        timeout=5000
                    )
                    await self.scroll_until_bottom()

                    try:
                        see_more_button = self.page.locator(
                            "button.infinite-scroller__show-more-button.infinite-scroller__show-more-button--visible"
                        )
                        await see_more_button.wait_for(state="visible", timeout=10000)
                        await see_more_button.scroll_into_view_if_needed()
                        await self.wait_random(0.1, 0.6)
                        await see_more_button.click()
                    except Exception as e:
                        self.logger.debug(
                            f"See more button not found or not clickable: {e}"
                        )
                        break

                    loaded_offers += OFFER_PER_CLICK

                    if loaded_offers >= MAX_JOBS_TO_FETCH:
                        break

                except Exception as e:
                    self.logger.error(f"Error scrolling through all jobs : {e}")
                    break

            await self._extract_jobs_urls_and_title_from_current_page()

        except Exception as e:
            raise ValueError(f"Error loading offers: {str(e)}")

        self.logger.info("Finished loading all available offers.")
        self.logger.info(f"Total URLs collected: {len(self._offers_urls)}")

    async def _get_total_offers_count(self) -> int:
        """Extract total offers count from LinkedIn's results header."""
        if not self.page:
            return 10
        try:
            small_element = self._get_locator(
                "span.results-context-header__job-count"
            ).first
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

    async def accept_cookies(self) -> None:
        """Accept LinkedIn cookies if the consent banner is present."""
        if not self.page:
            return
        try:
            accept_btn = self.page.locator(
                "button.artdeco-global-alert-action.artdeco-button.artdeco-button--inverse.artdeco-button--2.artdeco-button--primary[data-tracking-control-name='ga-cookie.consent.accept.v4']"
            )
            if await accept_btn.count() > 0 and await accept_btn.is_visible():
                await accept_btn.click()
                await self.wait_random(1, 2)
                self.logger.debug("Clicked LinkedIn cookie consent accept button.")
        except Exception as e:
            self.logger.debug(
                f"Cookie consent accept button not found or error clicking: {e}"
            )

    async def _extract_jobs_urls_and_title_from_current_page(self) -> int:  # noqa: C901
        if not self.page:
            return 0

        current_page_offers = 0

        try:
            job_items = self._get_locator("li:has(> div.base-card)")
            job_count = await job_items.count()

            for i in range(job_count):
                try:
                    job_item = job_items.nth(i)

                    title_link = job_item.locator("a.base-card__full-link").first

                    if await title_link.count() > 0:
                        job_title_element = title_link.locator("span.sr-only")
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

                            self.logger.debug(f"Extracted: {job_title} - {full_url}")

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
            next_button = self._get_locator(
                "//button[@aria-label='Voir la page suivante']"
            )
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
                await self._handle_popups()
                await self.wait_random(1, 3)

                # Title
                try:
                    title_el = self._get_locator(
                        "//h1[contains(@class, 'top-card-layout__title')]"
                    ).first
                    await title_el.wait_for(timeout=5000)
                    title = (await title_el.inner_html()).strip()
                except Exception as e:
                    self.logger.debug(f"Warning in getting jobTitle: {str(e)[:50]}")
                    title = offer.get("title", "N/A")

                # Company
                try:
                    company_el = self._get_locator(
                        "//a[contains(@class, 'topcard__org-name-link')]"
                    ).first
                    await company_el.wait_for(timeout=5000)
                    company = (await company_el.inner_text()).strip()
                except Exception as e:
                    self.logger.debug(f"Warning in getting jobCompany: {str(e)[:50]}")
                    company = "N/A"

                # Location
                try:
                    location_el = self._get_locator(
                        "//span[contains(@class, 'topcard__flavor') and contains(@class, 'topcard__flavor--bullet')]"
                    ).first
                    await location_el.wait_for(timeout=5000)
                    location = (await location_el.inner_text()).strip()
                except Exception as e:
                    self.logger.debug(f"Warning in getting location: {str(e)[:50]}")
                    location = "N/A"

                # Description
                try:
                    desc_full_el = self._get_locator(
                        "//div[contains(@class, 'description__text') and contains(@class, 'description__text--rich')]"
                    ).first
                    await desc_full_el.wait_for(timeout=5000)
                    description = (await desc_full_el.inner_text()).strip()
                except Exception as e:
                    self.logger.debug(
                        f"Warning in getting jobDescription: {str(e)[:50]}"
                    )
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
                self.logger.debug(f"Failed to extract data from URL: {offer['url']}")

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
        if not self.page:
            return
        try:
            btns = self.page.locator(
                "//button[contains(@class, 'modal__dismiss') and contains(@class, 'btn-tertiary')]"
            )
            count = await btns.count()
            for i in range(count):
                btn = btns.nth(i)
                if await btn.is_visible():
                    await btn.click()
                    await self.wait_random(1, 2)
        except Exception as e:
            self.logger.debug(f"No popup to dismiss or error handling popup: {e}")


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
        # headless=False,
        # debug=True,
    )

    job_offers = scraper.scrape()
    logger = logging.getLogger("job-tracker.linkedin-scraper")
    logger.info(f"Scraped {len(job_offers)} job offers from LinkedIn.")
    for offer in job_offers:
        logger.info(f"- {offer.title} at {offer.company} ({offer.location})")
