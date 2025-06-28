import re
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


class AppleJobScraper(JobScraperBase):
    """Apple Job Scraper using Playwright and Pydantic models."""

    def __init__(
        self,
        url: str,
        include_filters: Optional[List[str]] = None,
        exclude_filters: Optional[List[str]] = None,
        debug: bool = False,
        notion_client: Optional[NotionClient] = None,
        headless: bool = True,
    ):
        super().__init__(
            url=url,
            include_filters=include_filters,
            exclude_filters=exclude_filters,
            debug=debug,
            headless=headless,
        )
        self.notion_client = notion_client
        self.offers_urls = []

    async def extract_all_offers_url(self) -> None:  # noqa: C901
        """
        Load all offers by navigating through pagination.
        """
        if not self.page:
            raise RuntimeError("Page not initialized")

        try:
            await self.page.goto(self.url)
            await self.wait_random(2, 4)

            # Handle cookies
            try:
                cookie_btn = self.page.locator("#didomi-notice-agree-button")
                if await cookie_btn.count() > 0:
                    await cookie_btn.click()
                    await self.wait_random(1, 2)
                    # Reload page after accepting cookies like in Air France implementation
                    await self.page.reload()
                    await self.wait_random(1, 2)
            except Exception as e:
                if self.debug:
                    print(f"Could not handle cookies: {e}")

            # Get total offers count
            try:
                count_element = self.page.locator("#search-result-count")
                await count_element.wait_for(timeout=15000)
                count_text = await count_element.text_content()
                if count_text:
                    match = re.search(r"(\d+)", count_text)
                    if match:
                        total_offers = int(match.group(1))
                        print(f"Total offers found: {total_offers}")
                    else:
                        total_offers = 0
                else:
                    total_offers = 0
            except Exception as e:
                print(f"Could not determine total offers: {e}")
                total_offers = 0

            # Navigate through pages and collect offer URLs
            while True:
                try:
                    # Wait for job listings to load
                    await self.page.locator(
                        "li[data-core-accordion-item]"
                    ).first.wait_for(timeout=15000)

                    # Find all job containers
                    offer_rows = self.page.locator("li[data-core-accordion-item]")
                    offer_count = await offer_rows.count()

                    for i in range(offer_count):
                        try:
                            offer = offer_rows.nth(i)
                            title_link = offer.locator(
                                "a.link-inline.t-intro.word-wrap-break-word"
                            )

                            if await title_link.count() > 0:
                                job_title = await title_link.text_content()

                                if job_title and self.should_skip_offer_comprehensive(
                                    job_title=job_title.strip(),
                                    company="Apple",
                                    source=JobSource.APPLE,
                                    notion_client=self.notion_client,
                                ):
                                    continue

                                href = await title_link.get_attribute("href")
                                if href:
                                    # Construct full URL if needed
                                    if href.startswith("/"):
                                        full_url = f"https://jobs.apple.com{href}"
                                    else:
                                        full_url = href
                                    self.offers_urls.append(full_url)

                        except Exception as e:
                            print(f"Error extracting offer {i}: {e}")

                    print(f"{offer_count} offers loaded from current page")

                    # Try to navigate to next page
                    try:
                        next_button = self.page.locator(
                            "button.icon.icon-chevronend:not([disabled])"
                        )
                        if (
                            await next_button.count() > 0
                            and await next_button.is_enabled()
                        ):
                            await next_button.scroll_into_view_if_needed()
                            await next_button.click()
                            await self.wait_random(1.5, 2.5)
                            # Wait for new page to load
                            await self.page.locator(
                                "li[data-core-accordion-item]"
                            ).first.wait_for(timeout=10000)
                        else:
                            print("Reached last page or next button not available")
                            break
                    except Exception:
                        print("Reached last page or could not find next button")
                        break

                except Exception as e:
                    print(f"Error loading offers: {e}")
                    break

        except Exception as e:
            raise ValueError(f"Error loading offers: {str(e)}")

        print("Finished loading all available offers.")
        print(f"Total after filters: {len(self.offers_urls)}")

    async def parse_offers(self) -> List[JobOfferInput]:
        """
        Extract offers data from the collected URLs.

        Returns:
            List[JobOfferInput]: A list of JobOfferInput objects containing offer details.
        """
        if not self.page:
            raise RuntimeError("Page not initialized")

        offers = []

        for offer_url in self.offers_urls:
            try:
                await self.page.goto(offer_url)
                await self.wait_random(1, 3)

                # Extract offer data using the selectors from the working legacy code
                title = await self._safe_get_text("#jobdetails-postingtitle", "N/A")
                reference = await self._safe_get_text("#jobdetails-jobnumber", "N/A")
                location = await self._safe_get_text(
                    "#jobdetails-joblocation", "N/A", ",", 0
                )
                schedule_type = await self._safe_get_text(
                    "#jobdetails-weeklyhours", "N/A"
                )

                # Extract description from multiple sections exactly like the legacy code
                desc_parts = []
                desc_selectors = [
                    "#jobdetails-jobdetails-jobsummary-content-row",
                    "#jobdetails-jobdetails-jobdescription-content-row",
                    "#jobdetails-jobdetails-minimumqualifications-content-row",
                    "#jobdetails-jobdetails-preferredqualifications-content-row",
                ]

                for selector in desc_selectors:
                    desc = await self._safe_get_text(selector)
                    if desc and desc != "N/A":
                        desc_parts.append(desc)

                description = "\n".join(desc_parts) if desc_parts else "N/A"

                offer_input = JobOfferInput(
                    title=title,
                    company="Apple",
                    location=location,
                    contract_type=ContractType.CDI,  # Default for Apple
                    reference=reference,
                    schedule_type=schedule_type,
                    job_content_description=description,
                    source=JobSource.APPLE,
                    url=offer_url,
                    scraped_at=datetime.utcnow(),
                )

                offers.append(offer_input)
                if self.debug:
                    print(f"Apple offer extracted: {title} at Apple ({location})")

            except Exception as e:
                warnings.warn(f"Error extracting data for offer {offer_url}: {e}")
                if self.debug:
                    print(f"Failed to extract data from URL: {offer_url}")

        return offers


if __name__ == "__main__":
    # Example usage
    scraper = AppleJobScraper(
        url="https://jobs.apple.com/fr-fr/search?sort=relevance&location=france-FRAC",
        include_filters=["engineer", "software", "data"],
        exclude_filters=["intern", "internship"],
        debug=True,
        headless=False,
    )
    job_offers = scraper.scrape()
    print(f"Scraped {len(job_offers)} job offers from Apple.")
    for offer in job_offers:
        print(f"- {offer.title} at {offer.company} ({offer.location})")
