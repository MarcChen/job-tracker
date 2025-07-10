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
from services.scraping.src.base_model.job_scraper_base import JobScraperBase
from services.storage.src.notion_integration import NotionClient


class LinkedInJobScraper(JobScraperBase):
    """LinkedIn Job Scraper using Playwright and Pydantic models."""

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
        self.logger = logging.getLogger("job-tracker.linkedin-scraper")
        # Ensure _offers_urls is always a list
        if self._offers_urls is None:
            self._offers_urls = []

    async def extract_all_offers_url(self) -> None:  # noqa: C901
        """
        Load all offers by applying filters and navigating through pagination.
        """
        if not self.page:
            raise RuntimeError("Page not initialized")

        try:
            await self.page.goto(self.url)
            await self.wait_random(2, 4)
            # Handle potential cookie prompts and popups
            await self._handle_popups()

            # TODO: Implement login functionality if required
            # This should handle authentication to access more job listings
            await self._handle_login_if_required()

            # Apply keyword filter if provided
            if self.keyword:
                await self._apply_keyword_filter()

            # Apply location filter if provided
            if self.location:
                await self._apply_location_filter()

            # Get total offers count using the actual LinkedIn DOM structure
            total_offers = await self._get_total_offers_count()  # noqa: F84
            self.logger.info(
                f"Total offers found: {total_offers} for keyword '{self.keyword}' and location '{self.location}'"
            )

            # Navigate through pages and collect offer URLs
            page_number = 1
            while True:
                try:
                    # Wait for the main job list container to load (based on DOM structure)
                    await self.page.locator(
                        ".sPjpgbyxyDBHcovoUDFvkPFkSAMhQIJkP"
                    ).wait_for(timeout=10000)

                    # Extract job URLs from current page using the specific LinkedIn DOM structure
                    current_page_offers = await self._extract_jobs_from_current_page()

                    self.logger.info(
                        f"Page {page_number}: Extracted {current_page_offers} offers"
                    )

                    if current_page_offers == 0:
                        self.logger.warning("No offers found on current page, stopping")
                        break

                    # Navigate to next page using LinkedIn's pagination
                    if not await self._navigate_to_next_page():
                        self.logger.info("No more pages available")
                        break

                    page_number += 1

                except Exception as e:
                    self.logger.error(f"Error loading page {page_number}: {e}")
                    break

        except Exception as e:
            raise ValueError(f"Error loading offers: {str(e)}")

        # Filter out offers that already exist in Notion
        if self.notion_client:
            await self.filter_already_scraped_offers(self.notion_client)

        self.logger.info("Finished loading all available offers.")
        self.logger.info(f"Total URLs collected: {len(self._offers_urls)}")

    async def _handle_login_if_required(self) -> None:
        """Handle LinkedIn login if required using env vars."""
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
            # Wait for login form to appear
            await self.page.wait_for_selector("#session_key", timeout=10000)
            await self.page.wait_for_selector("#session_password", timeout=10000)
            # Fill email
            email_input = self.page.locator("#session_key")
            await email_input.fill(email)
            # Fill password
            password_input = self.page.locator("#session_password")
            await password_input.fill(password)
            # Click sign in
            submit_btn = self.page.locator('[data-id="sign-in-form__submit-btn"]')
            await submit_btn.click()
            self.logger.info("LinkedIn login submitted.")
            await self.wait_random(2, 4)
            # After login, check for suspicious login/verification challenge
            try:
                # Wait for main content to load
                await self.page.wait_for_selector("main.app__content", timeout=5000)
                # Check for the error banner and verification form
                error_banner = self.page.locator(".body__banner--error")
                verification_header = self.page.locator("h1.content__header")
                verification_form = self.page.locator("form#email-pin-challenge")
                if (
                    await error_banner.count() > 0
                    and await error_banner.is_visible()
                    and await verification_header.count() > 0
                    and "Let’s do a quick verification"
                    in (await verification_header.text_content() or "")
                    and await verification_form.count() > 0
                ):
                    self.logger.error(
                        "LinkedIn triggered suspicious login verification challenge. Manual intervention required."
                    )
                    raise RuntimeError(
                        "LinkedIn suspicious login verification challenge encountered."
                    )
            except Exception:
                pass
            self.logger.info("LinkedIn login successful.")
        except Exception as e:
            self.logger.error(f"LinkedIn login failed: {e}")

    async def _apply_keyword_filter(self) -> None:
        """Apply keyword filter using LinkedIn's search box."""
        if not self.page or not self.keyword:
            return
        try:
            keyword_input = self.page.locator('input[id*="jobs-search-box-keyword-id"]')
            if await keyword_input.count() > 0:
                await keyword_input.fill(self.keyword)
                await self.wait_random(0.5, 1.5)
                await keyword_input.press("Enter")
                self.logger.info(f"Applied keyword filter: {self.keyword}")
        except Exception as e:
            self.logger.warning(f"Could not apply keyword filter: {e}")

    async def _apply_location_filter(self) -> None:
        """Apply location filter using LinkedIn's search box."""
        if not self.page or not self.location:
            return
        try:
            location_input = self.page.locator(
                'input[id*="jobs-search-box-location-id"]'
            )
            if await location_input.count() > 0:
                await location_input.clear()
                await location_input.fill(self.location)
                await location_input.press("Enter")
                await self.wait_random(2, 3)
                self.logger.info(f"Applied location filter: {self.location}")
                return
        except Exception as e:
            self.logger.warning(f"Could not apply location filter: {e}")

    async def _get_total_offers_count(self) -> int:
        """Extract total offers count from LinkedIn's results header."""
        if not self.page:
            return 0
        try:
            await self.page.wait_for_selector(
                ".jobs-search-results-list__subtitle span[dir='ltr']",
                timeout=5000,
            )
            text = await self._safe_get_text(
                ".jobs-search-results-list__subtitle span[dir='ltr']", "N/A"
            )
            if text and text != "N/A":
                match = re.search(r"(\d+)", text.replace("\u202f", ""))
                if match:
                    return int(match.group(1))
            self.logger.warning("Could not find total offers count in DOM.")
        except Exception as e:
            self.logger.warning(f"Error extracting total offers count: {e}")
        return 0

    async def _extract_jobs_from_current_page(self) -> int:  # noqa: C901
        """Extract job URLs from the current page using LinkedIn's DOM structure."""
        if not self.page:
            return 0

        current_page_offers = 0

        try:
            # Based on the DOM structure: li elements with job-card-container
            job_items = self.page.locator("li[data-occludable-job-id]")
            job_count = await job_items.count()

            for i in range(job_count):
                try:
                    job_item = job_items.nth(i)

                    # Extract job title and URL from the specific LinkedIn structure
                    # Based on: <a class="disabled ember-view job-card-container__link" href="/jobs/view/4254887139/...">
                    title_link = job_item.locator("a.job-card-container__link").first

                    if await title_link.count() > 0:
                        # Get job title from the nested structure
                        job_title_element = title_link.locator(
                            "span[aria-hidden='true'] strong"
                        )
                        job_title = await self._safe_get_locator_text(
                            job_title_element, "N/A"
                        )

                        # Get href attribute
                        href = await title_link.get_attribute("href")

                        if href and job_title and job_title != "N/A":
                            # Apply filtering
                            if self.filter_job_title(job_title):
                                continue

                            # Construct full URL
                            if href.startswith("/"):
                                full_url = f"https://www.linkedin.com{href}"
                            else:
                                full_url = href

                            # Generate offer ID
                            offer_id = generate_job_offer_id(
                                "LinkedIn", job_title, full_url
                            )

                            self._offers_urls.append(
                                {"url": full_url, "id": offer_id, "title": job_title}
                            )
                            current_page_offers += 1

                            if self.debug:
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
        """Navigate to the next page using LinkedIn's pagination."""
        if not self.page:
            return False

        try:
            # Based on the DOM: <button aria-label="Voir la page suivante" class="...jobs-search-pagination__button jobs-search-pagination__button--next">
            next_selectors = [
                "button[aria-label*='Voir la page suivante']",
                "button[aria-label*='Next']",
                ".jobs-search-pagination__button--next",
                "button.jobs-search-pagination__button:has-text('Suivant')",
            ]

            for selector in next_selectors:
                next_button = self.page.locator(selector)
                if await next_button.count() > 0 and await next_button.is_enabled():
                    await next_button.scroll_into_view_if_needed()
                    await next_button.click()
                    await self.wait_random(2, 4)
                    return True

            return False

        except Exception as e:
            self.logger.info(f"Navigation to next page failed: {e}")
            return False

    async def parse_offers(self) -> List[JobOfferInput]:  # noqa: C901
        """
        Extract offers data from the collected URLs using LinkedIn's job detail page structure.

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

                # Wait for the main job details container to load
                try:
                    await self.page.locator(
                        ".job-details-jobs-unified-top-card__container"
                    ).wait_for(timeout=10000)
                except Exception:
                    # Fallback to alternative selectors
                    await self.page.locator(".jobs-unified-top-card").wait_for(
                        timeout=5000
                    )

                # Extract title using LinkedIn's specific DOM structure
                title = await self._extract_job_title()
                if title == "N/A":
                    title = offer.get("title", "N/A")

                # Extract company using LinkedIn's specific structure
                company = await self._extract_company_name()

                # Extract location using LinkedIn's specific structure
                location = await self._extract_job_location()

                # Extract job details (contract type, schedule type)
                contract_type_text, schedule_type = await self._extract_job_details()

                # Extract description using LinkedIn's job description structure
                description = await self._extract_job_description()

                # Map contract type to enum
                contract_type = self._map_contract_type(contract_type_text)

                # Extract reference/job ID from URL
                reference = self._extract_job_reference(offer["url"])

                offer_input = JobOfferInput(
                    title=title,
                    company=company,
                    location=location,
                    contract_type=contract_type,
                    reference=reference,
                    schedule_type=schedule_type,
                    job_content_description=description,
                    source=JobSource.LINKEDIN,
                    url=offer["url"],
                    scraped_at=datetime.utcnow(),
                )

                offers.append(offer_input)
                if self.debug:
                    self.logger.debug(
                        f"LinkedIn offer extracted: {title} at {company} ({location})"
                    )

            except Exception as e:
                warnings.warn(f"Error extracting data for offer {offer['url']}: {e}")
                if self.debug:
                    self.logger.debug(
                        f"Failed to extract data from URL: {offer['url']}"
                    )

        return offers

    async def _extract_job_title(self) -> str:
        """Extract job title from LinkedIn's job detail page."""
        if not self.page:
            return "N/A"

        # Based on the DOM: <h1 class="t-24 t-bold inline"><a href="...">Big Data Developer</a></h1>
        title_selectors = [
            ".job-details-jobs-unified-top-card__job-title h1 a",
            ".job-details-jobs-unified-top-card__job-title h1",
            ".jobs-unified-top-card__job-title h1",
            "h1.t-24.t-bold",
        ]

        for selector in title_selectors:
            title = await self._safe_get_text(selector, "N/A")
            if title != "N/A":
                return title.strip()

        return "N/A"

    async def _extract_company_name(self) -> str:
        """Extract company name from LinkedIn's job detail page."""
        if not self.page:
            return "N/A"

        # Based on the DOM: <div class="job-details-jobs-unified-top-card__company-name">
        company_selectors = [
            ".job-details-jobs-unified-top-card__company-name a",
            ".job-details-jobs-unified-top-card__company-name",
            ".jobs-unified-top-card__company-name a",
            ".jobs-unified-top-card__company-name",
        ]

        for selector in company_selectors:
            company = await self._safe_get_text(selector, "N/A")
            if company != "N/A":
                return company.strip()

        return "N/A"

    async def _extract_job_location(self) -> str:
        """Extract job location from LinkedIn's job detail page."""
        if not self.page:
            return "N/A"

        # Based on the DOM: location appears in the tertiary description container
        location_selectors = [
            ".job-details-jobs-unified-top-card__tertiary-description-container .tvm__text--low-emphasis",
            ".jobs-unified-top-card__bullet",
            ".job-details-jobs-unified-top-card__bullet",
        ]

        for selector in location_selectors:
            try:
                elements = self.page.locator(selector)
                count = await elements.count()
                for i in range(count):
                    text = await elements.nth(i).text_content()
                    if text and (
                        "France" in text
                        or "Paris" in text
                        or any(
                            city in text
                            for city in ["Lyon", "Marseille", "Toulouse", "Lille"]
                        )
                    ):
                        # Extract just the location part, remove extra info like "il y a X jours"
                        location_text = text.strip()
                        # Split by · and take the first part which should be location
                        if "·" in location_text:
                            location_text = location_text.split("·")[0].strip()
                        return location_text
            except Exception:
                continue

        return "N/A"

    async def _extract_job_details(self) -> tuple[str, str]:  # noqa: C901
        """Extract job details like contract type and schedule type."""
        if not self.page:
            return "CDI", "N/A"

        contract_type_text = "CDI"  # Default
        schedule_type = "N/A"

        try:
            # Look for job insights that contain employment type information
            # Based on: <span class="ui-label ui-label--accent-3">Hybride</span>
            insights = self.page.locator(
                ".job-details-jobs-unified-top-card__job-insight"
            )
            count = await insights.count()

            for i in range(count):
                insight_text = await insights.nth(i).text_content()
                if insight_text:
                    insight_lower = insight_text.lower()

                    # Check for work arrangement
                    if "hybride" in insight_lower or "hybrid" in insight_lower:
                        schedule_type = "Hybrid"
                    elif "remote" in insight_lower or "télétravail" in insight_lower:
                        schedule_type = "Remote"
                    elif "sur site" in insight_lower or "on-site" in insight_lower:
                        schedule_type = "On-site"
                    elif "temps plein" in insight_lower or "full-time" in insight_lower:
                        schedule_type = "Full-time"
                    elif (
                        "temps partiel" in insight_lower or "part-time" in insight_lower
                    ):
                        schedule_type = "Part-time"

                    # Check for contract type
                    if "cdd" in insight_lower or "contrat" in insight_lower:
                        contract_type_text = "CDD"
                    elif "stage" in insight_lower or "intern" in insight_lower:
                        contract_type_text = "Stage"
                    elif "freelance" in insight_lower:
                        contract_type_text = "Freelance"

        except Exception as e:
            self.logger.debug(f"Error extracting job details: {e}")

        return contract_type_text, schedule_type

    async def _extract_job_description(self) -> str:
        """Extract job description from LinkedIn's job detail page."""
        if not self.page:
            return "N/A"

        desc_parts = []

        try:
            # Main job description based on the DOM structure
            # <div class="jobs-box__html-content ... jobs-description-content__text--stretch">
            main_desc_selectors = [
                ".jobs-description__content .jobs-box__html-content",
                ".jobs-description-content__text",
                ".job-details-jobs-unified-top-card__primary-description-container",
                ".jobs-box__html-content",
            ]

            for selector in main_desc_selectors:
                desc = await self._safe_get_text(selector, "N/A")
                if (
                    desc != "N/A" and len(desc.strip()) > 50
                ):  # Ensure we get substantial content
                    desc_parts.append(desc.strip())
                    break  # Take the first substantial description found

            # Try to get additional description sections
            additional_selectors = [
                ".jobs-description__details",
                ".job-details-module .artdeco-card",
            ]

            for selector in additional_selectors:
                additional_desc = await self._safe_get_text(selector, "N/A")
                if (
                    additional_desc != "N/A"
                    and additional_desc not in desc_parts
                    and len(additional_desc.strip()) > 20
                ):
                    desc_parts.append(additional_desc.strip())

            description = "\n\n".join(desc_parts) if desc_parts else "N/A"

            # Clean up the description
            if description != "N/A":
                # Remove excessive whitespace
                description = " ".join(description.split())
                # Limit length to reasonable size
                if len(description) > 5000:
                    description = description[:5000] + "..."

            return description

        except Exception as e:
            self.logger.debug(f"Error extracting job description: {e}")
            return "N/A"

    def _map_contract_type(self, contract_type_text: str) -> ContractType:
        """Map contract type text to ContractType enum."""
        if not contract_type_text:
            return ContractType.CDI

        contract_type_lower = contract_type_text.lower()
        if (
            "cdd" in contract_type_lower
            or "temporary" in contract_type_lower
            or "contrat" in contract_type_lower
        ):
            return ContractType.CDD
        elif "stage" in contract_type_lower or "intern" in contract_type_lower:
            return ContractType.INTERNSHIP
        elif "freelance" in contract_type_lower:
            return ContractType.FREELANCE
        else:
            return ContractType.CDI

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

    notion_client = NotionClient(NOTION_API, DATABASE_ID)
    scraper = LinkedInJobScraper(
        url="https://www.linkedin.com/jobs/search/?keywords=ing%C3%A9nieur%20de%20donn%C3%A9es&location=Paris%20et%20p%C3%A9riph%C3%A9rie&f_TPR=r86400",
        keyword="ingénieur de données",
        location="Paris et périphérie",
        include_filters=["data", "engineer", "ingénieur", "données"],
        exclude_filters=["intern", "stage", "apprenti"],
        notion_client=notion_client,
        debug=True,
        headless=False,
    )

    job_offers = scraper.scrape()
    logger = logging.getLogger("job-tracker.linkedin-scraper")
    logger.info(f"Scraped {len(job_offers)} job offers from LinkedIn.")
    for offer in job_offers:
        logger.info(f"- {offer.title} at {offer.company} ({offer.location})")
