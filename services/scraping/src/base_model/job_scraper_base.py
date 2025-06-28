import asyncio
import random
import warnings
from typing import List, Optional

from playwright.async_api import Browser, Locator, Page, async_playwright

from services.scraping.src.base_model.job_offer import (
    JobOffer,
    JobOfferInput,
    JobSource,
)


class JobScraperBase:
    """Base class for job scrapers using Playwright and Pydantic models."""

    def __init__(
        self,
        url: str,
        browser: Optional[Browser] = None,
        include_filters: Optional[List[str]] = None,
        exclude_filters: Optional[List[str]] = None,
        debug: bool = False,
        headless: bool = True,
        slow_mo: int = 0,
    ):
        """
        Initialize the JobScraperBase class.

        Args:
            url (str): The URL of the job listing page to scrape.
            browser (Browser, optional): Playwright browser instance. If None, a new one will be created.
            include_filters (List[str], optional): Keywords that must be present in job titles.
            exclude_filters (List[str], optional): Keywords that should not be present in job titles.
            debug (bool): Enable debug logging.
            headless (bool): Run browser in headless mode.
            slow_mo (int): Slow down operations by specified milliseconds.
        """
        self.url = url
        self.browser = browser
        self.include_filters = include_filters or []
        self.exclude_filters = exclude_filters or []
        self.debug = debug
        self.headless = headless
        self.slow_mo = slow_mo

        # Internal state
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._browser_owned = False
        self._offer_urls_to_check = set()

    @property
    def page(self) -> Optional[Page]:
        """Get the current page instance."""
        return self._page

    async def _setup_browser(self) -> None:
        """Setup Playwright browser, context, and page."""
        if self.browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless, slow_mo=self.slow_mo
            )
            self._browser_owned = True
        else:
            self._browser = self.browser

        self._context = await self._browser.new_context()
        self._page = await self._context.new_page()

    async def _cleanup_browser(self) -> None:
        """Cleanup browser resources."""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser_owned and self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    def _init_offer_input(self) -> JobOfferInput:
        """Initialize a JobOfferInput with default values for missing fields."""
        from datetime import datetime

        return JobOfferInput(
            title="",
            company="",
            location="",
            source=JobSource.BUSINESS_FRANCE,
            url="",
            scraped_at=datetime.utcnow(),
        )

    def should_skip_offer(self, job_title: str) -> bool:
        """
        Determine if an offer should be skipped based on include/exclude filters.

        Args:
            job_title (str): The job title to check.

        Returns:
            bool: True if the offer should be skipped, False otherwise.
        """
        if self.include_filters and not any(
            keyword.lower() in job_title.lower() for keyword in self.include_filters
        ):
            print(f"Skipping offer '{job_title}' (doesn't match include filters)...")
            return True
        if self.exclude_filters and any(
            keyword.lower() in job_title.lower() for keyword in self.exclude_filters
        ):
            print(f"Skipping offer '{job_title}' (matches exclude filters)...")
            return True
        return False

    def should_skip_offer_comprehensive(
        self,
        job_title: str,
        company: str,
        source: JobSource,
        notion_client=None,
        include_filters: Optional[List[str]] = None,
        exclude_filters: Optional[List[str]] = None,
    ) -> bool:
        """
        Comprehensive check to determine if an offer should be skipped.
        Includes inclusion/exclusion filter checks and optional Notion database existence check.

        Args:
            job_title (str): The job title to check.
            company (str): The company name for Notion existence check.
            source (str): The source name for Notion existence check.
            notion_client: Optional Notion client for checking if offer already exists.
            include_filters (List[str], optional): Override include filters. If None, uses instance filters.
            exclude_filters (List[str], optional): Override exclude filters. If None, uses instance filters.

        Returns:
            bool: True if the offer should be skipped, False otherwise.
        """
        # Use provided filters or fall back to instance filters
        active_include_filters = (
            include_filters if include_filters is not None else self.include_filters
        )
        active_exclude_filters = (
            exclude_filters if exclude_filters is not None else self.exclude_filters
        )

        # Check inclusion filters - skip if job title doesn't match any include filter
        if active_include_filters and not any(
            keyword.lower() in job_title.lower() for keyword in active_include_filters
        ):
            print(
                f"Skipping offer '{job_title}' (doesn't match include filters: {active_include_filters})..."
            )
            return True

        # Check exclusion filters - skip if job title matches any exclude filter
        if active_exclude_filters and any(
            keyword.lower() in job_title.lower() for keyword in active_exclude_filters
        ):
            print(
                f"Skipping offer '{job_title}' (matches exclude filters: {active_exclude_filters})..."
            )
            return True

        # Check if offer already exists in Notion (if client provided)
        if notion_client and hasattr(notion_client, "offer_exists"):
            try:
                if notion_client.offer_exists(
                    title=job_title, source=source, company=company
                ):
                    print(
                        f"Skipping offer '{job_title}' (already exists in Notion database)..."
                    )
                    return True
            except Exception as e:
                if self.debug:
                    print(
                        f"Warning: Failed to check Notion existence for '{job_title}': {e}"
                    )

        return False

    def convert_to_job_offer(self, offer_input: JobOfferInput) -> Optional[JobOffer]:
        """
        Convert a JobOfferInput to a validated JobOffer.

        Args:
            offer_input (JobOfferInput): The input data to convert.

        Returns:
            JobOffer or None: The validated job offer, or None if validation fails.
        """
        try:
            return offer_input.to_job_offer()
        except Exception as e:
            warnings.warn(f"Failed to convert offer input to JobOffer: {e}")
            if self.debug:
                print(f"Problematic offer input: {offer_input}")
            return None

    # Utility methods for common Playwright operations
    async def wait_random(
        self, min_seconds: float = 1.0, max_seconds: float = 3.0
    ) -> None:
        """Wait for a random amount of time."""
        wait_time = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(wait_time)

    async def scroll_into_view(self, locator: str) -> None:
        """Scroll an element into view."""
        if self._page:
            await self._page.locator(locator).scroll_into_view_if_needed()

    async def safe_click(self, locator: str, timeout: int = 5000) -> bool:
        """
        Safely click an element with timeout.

        Returns:
            bool: True if click succeeded, False otherwise.
        """
        try:
            if self._page:
                await self._page.locator(locator).click(timeout=timeout)
                return True
        except Exception as e:
            if self.debug:
                print(f"Failed to click {locator}: {e}")
        return False

    async def _safe_get_text(
        self,
        selector: str,
        default: str = "N/A",
        split_by: Optional[str] = None,
        split_index: Optional[int] = None,
    ) -> str:
        """
        Safely get text from a CSS selector with error handling and optional splitting.

        Args:
            selector (str): CSS selector for the element.
            default (str): Default value to return if element not found or empty.
            split_by (str, optional): Text to split by. If provided, will split the text.
            split_index (int, optional): Index of the split part to return. Required if split_by is provided.

        Returns:
            str: The text content of the element (optionally split), or default value.
        """
        try:
            if self._page:
                element = self._page.locator(selector)
                if await element.count() > 0:
                    text = await element.text_content()
                    if text:
                        text = text.strip()
                        # Handle splitting if parameters are provided
                        if split_by is not None and split_index is not None:
                            if split_by in text:
                                parts = text.split(split_by)
                                if len(parts) > split_index:
                                    return parts[split_index].strip()
                                else:
                                    return default
                            else:
                                return default
                        return text
                    else:
                        return default
        except Exception as e:
            if self.debug:
                print(f"Failed to get text from selector {selector}: {e}")
        return default

    async def _safe_get_locator_text(
        self, locator: Locator, default: str = "N/A"
    ) -> str:
        """
        Safely get text from a Playwright locator with error handling.

        Args:
            locator (Locator): Playwright locator object.
            default (str): Default value to return if element not found or empty.

        Returns:
            str: The text content of the element, or default value.
        """
        try:
            if await locator.count() > 0:
                text = await locator.text_content()
                return text.strip() if text else default
        except Exception as e:
            if self.debug:
                print(f"Failed to get text from locator: {e}")
        return default

    async def _safe_get_attribute(
        self, selector: str, attribute: str, default: str = ""
    ) -> str:
        """
        Safely get an attribute value from a CSS selector with error handling.

        Args:
            selector (str): CSS selector for the element.
            attribute (str): Name of the attribute to get.
            default (str): Default value to return if element not found or attribute missing.

        Returns:
            str: The attribute value, or default value.
        """
        try:
            if self._page:
                element = self._page.locator(selector)
                if await element.count() > 0:
                    attr_value = await element.get_attribute(attribute)
                    return attr_value if attr_value is not None else default
        except Exception as e:
            if self.debug:
                print(
                    f"Failed to get attribute {attribute} from selector {selector}: {e}"
                )
        return default

    # Abstract methods that subclasses must implement
    async def extract_all_offers_url(self) -> None:
        """
        Load all offers by navigating through pagination or load-more buttons.
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    async def parse_offers(self) -> List[JobOfferInput]:
        """
        Extract offers data from the loaded page.

        Returns:
            List[JobOfferInput]: A list of JobOfferInput objects containing scraped data.
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    async def scrape_async(self) -> List[JobOffer]:
        """
        Perform the async scraping process.

        Returns:
            List[JobOffer]: A list of validated JobOffer objects.
        """
        await self._setup_browser()
        try:
            await self.extract_all_offers_url()
            raw_offers = await self.parse_offers()

            validated_offers = []
            for offer_input in raw_offers:
                job_offer = self.convert_to_job_offer(offer_input)
                if job_offer:
                    validated_offers.append(job_offer)

            if self.debug:
                print(
                    f"Scraped {len(validated_offers)} valid offers out of {len(raw_offers)} total"
                )

            return validated_offers
        finally:
            await self._cleanup_browser()

    def scrape(self) -> List[JobOffer]:
        """
        Perform the synchronous scraping process.

        Returns:
            List[JobOffer]: A list of validated JobOffer objects.
        """
        return asyncio.run(self.scrape_async())
