import logging
import warnings
from datetime import datetime
from typing import List, Optional

from services.scraping.src.base_model.job_offer import (
    ContractType,
    JobOfferInput,
    JobSource,
    generate_job_offer_id,
    pre_process_url,
)
from services.scraping.src.base_model.job_scraper_base import JobScraperBase
from services.storage.src.notion_integration import NotionClient


class WelcomeToTheJungleJobScraper(JobScraperBase):
    """Welcome to the Jungle Job Scraper using Playwright and Pydantic models."""

    def __init__(
        self,
        url: str,
        notion_client: NotionClient,
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
        self.logger = logging.getLogger("job-tracker.wttj-scraper")

    async def extract_all_offers_url(self) -> None:  # noqa: C901
        """
        Load all offers by applying filters and navigating through pagination.
        """
        if not self.page:
            raise RuntimeError("Page not initialized")

        await self.page.goto(self.url)

        # Handle cookies and banners
        await self._handle_popups()

        # Apply location filter
        if self.location:
            try:
                location_input = self.page.locator("#search-location-field")
                # Clear existing location
                clear_button = self.page.locator(
                    "button[data-testid='clear-dropdown-search']"
                )
                if await clear_button.count() > 0:
                    await clear_button.click()

                await location_input.fill(self.location)
                await self.wait_random(1, 1.5)
                await location_input.press("Enter")
                await self.wait_random(1, 2)
                self.logger.info(f"applied location filter: {self.location}")
            except Exception as e:
                await self.save_error_screenshot("wtj-location_filter_error")
                self.logger.warning(f"Could not apply location filter: {e}")

        # Apply keyword filter
        if self.keyword:
            try:
                search_input = self.page.locator("#search-query-field")
                await search_input.clear()
                await search_input.fill(self.keyword)
                await search_input.press("Enter")
                await self.wait_random(1, 2)
                self.logger.info(f"applied keyword filter: {self.keyword}")
            except Exception as e:
                await self.save_error_screenshot("wtj-keyword_filter_error")
                self.logger.warning(f"Could not apply keyword filter: {e}")

        # Get total offers count
        try:
            count_element = self.page.locator(
                "div[data-testid='jobs-search-results-count']"
            )
            await count_element.wait_for(timeout=10000)
            count_text = await count_element.text_content()
            if count_text:
                total_offers = int(count_text.strip())
                self.logger.info(f"Total offers found: {total_offers}")
            else:
                total_offers = 0
        except Exception as e:
            await self.save_error_screenshot("wtj-total_offers_count_error")
            self.logger.warning(f"Could not determine total offers: {e}")
            total_offers = 0

        loaded_offers = 0

        # Navigate through pages and collect offer URLs
        while loaded_offers < total_offers:
            try:
                # Wait for offers to load
                await self.page.locator(
                    "li[data-testid='search-results-list-item-wrapper']"
                ).first.wait_for(timeout=10000)

                offer_rows = self.page.locator(
                    "li[data-testid='search-results-list-item-wrapper']"
                )
                offer_count = await offer_rows.count()

                for i in range(offer_count):
                    try:
                        offer = offer_rows.nth(i)
                        # Look for job title link within the offer - specifically the one with h2 tag
                        title_links = offer.locator("a[href*='/jobs/'] h2")

                        if await title_links.count() > 0:
                            # Get the parent <a> tag
                            title_link = title_links.first.locator("..")
                            job_title = await title_links.first.text_content()
                            loaded_offers += 1

                            if job_title and not self.filter_job_title(
                                job_title=job_title,
                                include_filters=self.include_filters,
                                exclude_filters=self.exclude_filters,
                            ):
                                href = await title_link.get_attribute("href")
                                if href:
                                    # Make sure URL is absolute
                                    if href.startswith("/"):
                                        href = (
                                            "https://www.welcometothejungle.com" + href
                                        )
                                    company_element = offer.locator("span.wui-text")
                                    company = await company_element.text_content()
                                    company = company.strip()
                                    self.logger.debug(f"Company name : {company}")
                                    self._offers_urls.append(
                                        {
                                            "url": pre_process_url(href),
                                            "id": generate_job_offer_id(
                                                company=company.strip(),
                                                title=job_title.strip(),
                                                url=pre_process_url(href),
                                            ),
                                        }
                                    )
                                    self.logger.debug(
                                        f"Added offer URL: {href}" if self.debug else ""
                                    )

                    except Exception as e:
                        self.logger.debug(f"Error extracting offer {i}: {e}")

                self.logger.debug(f"Loaded {loaded_offers} offers")

                if loaded_offers >= total_offers:
                    break

                # Try to navigate to next page
                try:
                    # Find pagination nav and next button
                    pagination_nav = self.page.locator("nav[aria-label='Pagination']")
                    if await pagination_nav.count() > 0:
                        # Find the last li element (next button)
                        pagination_items = pagination_nav.locator("li")
                        pagination_count = await pagination_items.count()

                        if pagination_count > 0:
                            next_button_li = pagination_items.nth(pagination_count - 1)
                            next_button = next_button_li.locator("a")

                            if await next_button.count() > 0:
                                # Scroll into view and click
                                await next_button.scroll_into_view_if_needed()
                                await self.wait_random(1, 2)
                                await next_button.click()
                                await self.wait_random(1, 3)
                            else:
                                self.logger.info("Reached last page")
                                break
                        else:
                            self.logger.info("No pagination items found")
                            break
                    else:
                        self.logger.info("No pagination nav found")
                        break
                except Exception:
                    self.logger.info("Reached last offer or pagination failed")
                    break

            except Exception as e:
                self.logger.error(f"Error loading offers: {e}")
                break

        self.logger.info(
            f"Finished loading all available offers. Total URLs collected: {len(self._offers_urls)}"
        )

    async def parse_offers(self) -> List[JobOfferInput]:  # noqa: C901
        """
        Extract offers data from the collected URLs.

        Returns:
            List[JobOfferInput]: A list of JobOfferInput objects containing offer details.
        """
        if not self.page:
            raise RuntimeError("Page not initialized")

        offers = []

        for offer in self._offers_urls:
            try:
                await self.page.goto(offer["url"])
                await self.wait_random(1, 3)

                # Extract title using base class method
                title = await self._safe_get_text(
                    "div[data-testid='job-metadata-block'] h2"
                )
                if title == "N/A":
                    title = await self._safe_get_text("h2[class*='wui-text']")

                # Extract company name using base class method
                company = await self._safe_get_text(
                    "div[data-testid='job-metadata-block'] a[href*='/companies/'] span[class*='wui-text']"
                )

                # Extract location using CSS selector with descendant span
                # First try to get the main location text from the parent span
                location = await self._safe_get_text(
                    "div[data-testid='job-metadata-block'] i[name='location'] + span"
                )
                if location == "N/A":
                    # Alternative selector - try the specific location div structure
                    location = await self._safe_get_text(
                        "div[data-testid='job-metadata-block'] div.sc-fibHhp:has(i[name='location']) span.sc-hNNPnn"
                    )
                    if location == "N/A":
                        # Last fallback - try to get first location span only
                        location_element = self.page.locator(
                            "div[data-testid='job-metadata-block'] i[name='location'] + span span"
                        ).first
                        if await location_element.count() > 0:
                            location = await location_element.text_content()
                            location = location.strip() if location else "N/A"

                # Extract contract type using more specific CSS selector
                contract_full_text = await self._safe_get_text(
                    "div[data-testid='job-metadata-block'] div.sc-fibHhp:has(i[name='contract'])"
                )
                contract_type_text = "CDI"  # Default
                if contract_full_text != "N/A":
                    # Extract contract type from the text
                    if "Stage" in contract_full_text:
                        contract_type_text = "Stage"
                    elif "CDD" in contract_full_text:
                        contract_type_text = "CDD"
                    elif "CDI" in contract_full_text:
                        contract_type_text = "CDI"
                    elif "Freelance" in contract_full_text:
                        contract_type_text = "Freelance"

                # Extract salary using more specific CSS selector and text splitting
                salary = await self._safe_get_text(
                    "div[data-testid='job-metadata-block'] div.sc-fibHhp:has(i[name='salary'])",
                    split_by="Salaire : ",
                    split_index=1,
                )
                if salary == "N/A":
                    # Fallback - extract full text and parse manually
                    salary_full = await self._safe_get_text(
                        "div[data-testid='job-metadata-block'] div.sc-fibHhp:has(i[name='salary'])"
                    )
                    if salary_full != "N/A" and "Salaire :" in salary_full:
                        parts = salary_full.split("Salaire :")
                        salary = parts[1].strip() if len(parts) > 1 else "N/A"

                # Extract experience level (not present in this example, but keeping for compatibility)
                experience = "N/A"
                experience_full = await self._safe_get_text(
                    "div[data-testid='job-metadata-block'] div.sc-fibHhp:has(i[name='suitcase'])"
                )
                if experience_full != "N/A" and "Expérience :" in experience_full:
                    parts = experience_full.split("Expérience :")
                    experience = parts[1].strip() if len(parts) > 1 else "N/A"

                # Extract remote work info using more specific CSS selector
                remote_work = await self._safe_get_text(
                    "div[data-testid='job-metadata-block'] div.sc-fibHhp:has(i[name='remote']) span:not(.sc-brzPDJ)"
                )
                if remote_work == "N/A":
                    # Alternative selector - try without the :not() pseudo-class
                    remote_work = await self._safe_get_text(
                        "div[data-testid='job-metadata-block'] i[name='remote'] + span"
                    )

                # Extract description parts using base class method
                desc_post = await self._safe_get_text(
                    "div[data-testid='job-section-description']"
                )
                desc_experience = await self._safe_get_text(
                    "div[data-testid='job-section-experience']"
                )
                desc_process = await self._safe_get_text(
                    "div[data-testid='job-section-process']"
                )

                # Build description like in the Selenium version
                lines = []
                if remote_work != "N/A" and remote_work != "Télétravail non renseigné":
                    lines.append(f"Remote : {remote_work}")
                if desc_post != "N/A":
                    lines.append(f"Job Description:\n{desc_post}")
                if desc_experience != "N/A":
                    lines.append(f"Required Profile:\n{desc_experience}")
                if desc_process != "N/A":
                    lines.append(f"Interview Process:\n{desc_process}")

                description = "\n\n".join(lines) if lines else "N/A"

                # Map contract type to enum
                contract_type = ContractType.CDI
                if contract_type_text and contract_type_text != "N/A":
                    contract_type_lower = contract_type_text.lower()
                    if "cdd" in contract_type_lower:
                        contract_type = ContractType.CDD
                    elif (
                        "stage" in contract_type_lower
                        or "intern" in contract_type_lower
                    ):
                        contract_type = ContractType.INTERNSHIP
                    elif "freelance" in contract_type_lower:
                        contract_type = ContractType.FREELANCE

                offer_input = JobOfferInput(
                    title=title or "N/A",
                    company=company or "N/A",
                    location=location or "N/A",
                    contract_type=contract_type,
                    salary=salary or "N/A",
                    job_content_description=description,
                    source=JobSource.WELCOME_TO_THE_JUNGLE,
                    url=offer["url"],
                    scraped_at=datetime.utcnow(),
                )

                offers.append(offer_input)

                if self.debug:
                    self.logger.debug("WTTJ offer extracted:")
                    self.logger.debug(f"  Title: {title}")
                    self.logger.debug(f"  Company: {company}")
                    self.logger.debug(f"  Location: {location}")
                    self.logger.debug(
                        f"  Contract: {contract_type_text} -> {contract_type}"
                    )
                    self.logger.debug(f"  Salary: {salary}")
                    self.logger.debug(f"  Experience: {experience}")
                    self.logger.debug(f"  Remote: {remote_work}")
                    self.logger.debug(f"  URL: {offer['url']}")
                else:
                    self.logger.info(f"WTTJ offer extracted: {title} at {company}")

            except Exception as e:
                warnings.warn(f"Error extracting data for offer {offer['url']}: {e}")

        return offers

    async def _handle_popups(self) -> None:
        """Handle cookies and other popups."""
        if not self.page:
            return

        # Handle cookie banners
        cookie_selectors = [
            "#axeptio_btn_dismiss",
            "#axeptio_btn_configure",
            "#axeptio_btn_acceptAll",
        ]

        for selector in cookie_selectors:
            try:
                cookie_btn = self.page.locator(selector)
                if await cookie_btn.count() > 0:
                    await cookie_btn.click()
                    await self.wait_random(1, 2)
                    break
            except Exception:
                continue

        # Handle country banner
        try:
            french_btn = self.page.locator(
                "button[data-testid='country-banner-stay-button']"
            )
            if await french_btn.count() > 0:
                await french_btn.click()
                await self.wait_random(1, 2)
        except Exception:
            pass


if __name__ == "__main__":
    import os

    DATABASE_ID = os.getenv("DATABASE_ID")
    NOTION_API = os.getenv("NOTION_API")
    assert DATABASE_ID, "DATABASE_ID environment variable is not set."
    assert NOTION_API, "NOTION_API environment variable is not set."
    notion_client = NotionClient(NOTION_API, DATABASE_ID)
    scraper = WelcomeToTheJungleJobScraper(
        url="https://www.welcometothejungle.com/fr/jobs?&refinementList%5Bcontract_type%5D%5B%5D=full_time&refinementList%5Bcontract_type%5D%5B%5D=temporary&refinementList%5Bcontract_type%5D%5B%5D=freelance",
        keyword="Pyspark",
        location="Paris",
        include_filters=["Data"],
        exclude_filters=["alternance", "stage", "apprenti"],
        notion_client=notion_client,
        debug=True,
        headless=False,
    )
    job_offers = scraper.scrape()
    print(f"Scraped {len(job_offers)} job offers from Welcome to the Jungle.")
    for offer in job_offers:
        print(f"- {offer.title} at {offer.company} ({offer.location})")
