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

    async def extract_all_offers_url(self) -> None:
        """
        Load all offers by repeatedly clicking 'Voir Plus d'Offres' with added randomness.
        """
        if not self.page:
            raise RuntimeError("Page not initialized")

        await self.page.goto(self.url)
        await self.wait_random(3, 6)  # Randomized initial wait

        previous_count = 0

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
                await self.wait_random(1.5, 2.5)  # Randomized wait

                # Check if the count of offers has increased
                offer_elements = self.page.locator(".figure-item")
                current_count = await offer_elements.count()

                if current_count == previous_count:
                    print("No new offers detected. Assuming all offers are loaded.")
                    break
                else:
                    previous_count = current_count
                    print(f"Loaded {current_count} offers so far.")

            except Exception as e:
                print(f"Reached last offer or button not found: {e}")
                break

        print("Finished loading all available offers.")

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
                title = await self._safe_get_locator_text(offer.locator("h2"), "N/A")
                company = await self._safe_get_locator_text(
                    offer.locator(".organization"), "N/A"
                )
                location = await self._safe_get_locator_text(
                    offer.locator(".location"), "N/A"
                )

                # Apply comprehensive filtering (includes filters + Notion existence check)
                if self.filter_job_title(
                    job_title=title,
                    include_filters=self.include_filters,
                    exclude_filters=self.exclude_filters,
                ):
                    continue

                # Extract details from list items
                details_elements = offer.locator("li")
                details_count = await details_elements.count()

                contract_type = ContractType.VIE
                duration = "N/A"

                if details_count > 1:
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
                (
                    print(f"VIE offer extracted: {title} at {company}")
                    if self.debug
                    else None
                )

            except Exception as e:
                warnings.warn(f"Error extracting data for offer {i}: {e}")

        return offers


if __name__ == "__main__":
    import os

    DATABASE_ID = os.getenv("DATABASE_ID")
    NOTION_API = os.getenv("NOTION_API")
    assert DATABASE_ID, "DATABASE_ID environment variable is not set."
    assert NOTION_API, "NOTION_API environment variable is not set."
    notion_client = NotionClient(NOTION_API, DATABASE_ID)
    scraper = VIEJobScraper(
        url="https://mon-vie-via.businessfrance.fr/offres/recherche?query=Data%20Engineer",
        include_filters=["data", "engineer", "software"],
        exclude_filters=["intern", "stage"],
        notion_client=notion_client,
        debug=True,
        headless=False,  # Set to True for production
    )
    job_offers = scraper.scrape()
    print(f"Scraped {len(job_offers)} job offers.")
    print(job_offers)
