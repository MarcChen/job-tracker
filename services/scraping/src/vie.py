import logging
import warnings
from datetime import datetime
from typing import List, Optional

from services.scraping.src.base_model.job_offer import (
    ContractType,
    JobOfferInput,
    JobSource,
)
from services.scraping.src.base_model.job_scraper_base import JobScraperBase
from services.storage.src.notion_integration import NotionClient


class VIEJobScraper(JobScraperBase):
    """VIE Job Scraper using Playwright and Pydantic models."""

    def __init__(
        self,
        url: str,
        notion_client: NotionClient,
        include_filters: Optional[List[str]] = None,
        exclude_filters: Optional[List[str]] = None,
        debug: bool = False,
        headless: bool = True,
    ):
        super().__init__(
            url=url,
            notion_client=notion_client,
            include_filters=include_filters,
            exclude_filters=exclude_filters,
            debug=debug,
            headless=headless,
        )
        self._offers_urls = []
        self.logger = logging.getLogger("job-tracker.vie-scraper")

    async def extract_all_offers_url(self) -> None:
        """
        Load all offers by repeatedly clicking 'Voir Plus d'Offres' with added randomness.
        """
        if not self.page:
            raise RuntimeError("Page not initialized")

        await self.page.goto(self.url)
        await self.wait_random(3, 6)  # Randomized initial wait

        # Handle Didomi cookie consent popup
        try:
            # Wait for the accept button to appear
            accept_button = self.page.locator("#didomi-notice-agree-button")
            await accept_button.wait_for(state="visible", timeout=5000)
            await accept_button.click()
            self.logger.info("Clicked cookie consent accept button")
            await self.wait_random(1, 2)
        except Exception as e:
            self.logger.info(f"Cookie consent popup not found or already accepted: {e}")

        await self.wait_random(1, 2)

        previous_count = 0
        no_change_attempts = 0  # Track consecutive attempts with no new offers
        max_attempts = 3  # Maximum retry attempts

        while True:
            try:
                # Check if the "Voir Plus d'Offres" button is still clickable
                see_more_button = self.page.locator(".see-more-btn")

                # Wait for button to be visible and clickable
                await see_more_button.wait_for(state="visible", timeout=5000)

                # Scroll into view and click
                await see_more_button.scroll_into_view_if_needed()
                await self.wait_random(1, 2)  # Randomized scroll wait
                await see_more_button.click()

                # Wait for new offers to load
                await self.wait_random(5, 8)  # Randomized wait

                # Check if the count of offers has increased
                offer_elements = self.page.locator(".figure-item")
                current_count = await offer_elements.count()

                if current_count == previous_count:
                    no_change_attempts += 1
                    self.logger.info(
                        f"No new offers detected (attempt {no_change_attempts}/{max_attempts})."
                    )
                    if no_change_attempts >= max_attempts:
                        self.logger.info("Assuming all offers are loaded.")
                        break
                else:
                    no_change_attempts = 0  # Reset counter when new offers are found
                    previous_count = current_count
                    self.logger.info(f"Loaded {current_count} offers so far.")
            except Exception as e:
                self.logger.info(f"Reached last offer or button not found: {e}")
                await self.save_error_screenshot("vie-offers-error")
                break
        self.logger.info("Finished loading all available offers.")

    async def parse_offers(self) -> List[JobOfferInput]:
        """
        Extract offers data from the loaded page.

        Returns:
            List[JobOfferInput]: A list of JobOfferInput objects containing offer details.
        """
        if not self.page:
            raise RuntimeError("Page not initialized")

        offers = []
        offer_elements = self.page.locator(".figure-item")
        offer_count = await offer_elements.count()

        for i in range(offer_count):
            offer = offer_elements.nth(i)

            try:
                await self.wait_random(0.1, 0.3)  # Randomized delay per offer

                # Extract basic fields
                title = await self._safe_get_locator_text(
                    offer.locator("h2.mission-title"), "N/A"
                )
                company = await self._safe_get_locator_text(
                    offer.locator("h3.organization-name"), "N/A"
                )
                location = await self._safe_get_locator_text(
                    offer.locator("h2.location"), "N/A"
                )

                # Apply comprehensive filtering (includes filters + Notion existence check)
                if self.filter_job_title(
                    job_title=title,
                    include_filters=self.include_filters,
                    exclude_filters=self.exclude_filters,
                ):
                    continue

                # Extract details from list items
                details_elements = offer.locator("ul.meta-list > li")
                details_count = await details_elements.count()

                contract_type = ContractType.VIE
                duration = "N/A"

                if details_count > 0:
                    # First li is usually the contract type (VIE/VIA)
                    type_text = await self._safe_get_locator_text(
                        details_elements.nth(0), "N/A"
                    )
                    if "VIA" in type_text.upper():
                        contract_type = ContractType.VIA

                if details_count > 1:
                    # Second li is usually the duration
                    duration = await self._safe_get_locator_text(
                        details_elements.nth(1), "N/A"
                    )

                offer_input = JobOfferInput(
                    title=title,
                    company=company,
                    location=location,
                    contract_type=contract_type,
                    duration=duration,
                    source=JobSource.BUSINESS_FRANCE,
                    url=self.url,
                    scraped_at=datetime.utcnow(),
                )

                offers.append(offer_input)
                if self.debug:
                    self.logger.debug(f"VIE offer extracted: {title} at {company}")
            except Exception as e:
                warnings.warn(f"Error extracting data for offer {i}: {e}")

        return offers


if __name__ == "__main__":
    import os
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    DATABASE_ID = os.getenv("DATABASE_ID")
    NOTION_API = os.getenv("NOTION_API")

    notion_client = None
    if DATABASE_ID and NOTION_API:
        notion_client = NotionClient(NOTION_API, DATABASE_ID)
    else:
        logging.error(
            "DATABASE_ID or NOTION_API not set. Notion export will be skipped."
        )

    scraper = VIEJobScraper(
        url="https://mon-vie-via.businessfrance.fr/offres/recherche?query=Data%20Engineer",
        include_filters=["data", "engineer", "software"],
        exclude_filters=["intern", "stage"],
        notion_client=notion_client,
        headless=True,
    )

    job_offers = scraper.scrape()
    logging.getLogger("job-tracker.vie-scraper").info(
        f"Scraped {len(job_offers)} job offers."
    )
    # Print offers to stdout for verification
    for offer in job_offers:
        print(f"- {offer.title} ({offer.company}) [{offer.location}]")
