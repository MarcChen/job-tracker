import asyncio
import logging
import os
import random
import warnings
from datetime import datetime
from typing import List, Optional

from playwright.async_api import Browser, Locator, Page, async_playwright
from playwright_stealth import Stealth, ALL_EVASIONS_DISABLED_KWARGS

from services.scraping.src.base_model.job_offer import (
    JobOffer,
    JobOfferInput,
    JobSource,
)
from services.storage.src.notion_integration import NotionClient


class JobScraperBase:
    """Base class for job scrapers using Playwright and Pydantic models."""

    def __init__(
        self,
        url: str,
        notion_client: NotionClient,
        _offers_urls: Optional[
            List[dict]
        ] = None,  # Each offer: {"url": ..., "id": ...}
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
            _offers_urls (List[dict], optional): List of _offers_urls, each as {"url": ..., "id": ...}.
            browser (Browser, optional): Playwright browser instance. If None, a new one will be created.
            include_filters (List[str], optional): Keywords that must be present in job titles.
            exclude_filters (List[str], optional): Keywords that should not be present in job titles.
            debug (bool): Enable debug logging.
            headless (bool): Run browser in headless mode.
            slow_mo (int): Slow down operations by specified milliseconds.
        """
        self.url = url
        self._offers_urls = _offers_urls
        self.browser = browser
        self.include_filters = include_filters or []
        self.exclude_filters = exclude_filters or []
        self.debug = debug
        self.headless = headless
        self.slow_mo = slow_mo
        self.notion_client = notion_client
        self.logger = logging.getLogger("job-tracker.base-scraper")

        # Internal state
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._browser_owned = False

    @property
    def page(self) -> Optional[Page]:
        """Get the current page instance."""
        return self._page

    async def _setup_browser(self) -> None:
        """Setup Playwright browser, context, and page with custom user-agent and headers for anti-bot evasion."""
        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
        extra_headers = {
            "Accept-Language": "fr-FR,fr;q=0.9",
            # Ajoutez d'autres en-têtes si nécessaire
        }
        custom_languages = ("fr-FR", "fr")
        stealth = Stealth(
            navigator_languages_override=custom_languages,
            init_scripts_only=True
        )

        if self.browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless, slow_mo=self.slow_mo
            )
            self._browser_owned = True
        else:
            self._browser = self.browser

        self._context = await self._browser.new_context(
            user_agent=user_agent,
            extra_http_headers=extra_headers,
        )
        await stealth.apply_stealth_async(self._context)
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
        return JobOfferInput(
            title="",
            company="",
            location="",
            source=JobSource.UNKNOWN,
            url="",
            scraped_at=datetime.utcnow(),
        )

    def filter_job_title(
        self,
        job_title: str,
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
            self.logger.debug(
                f"Skipping offer '{job_title}' (doesn't match include filters: {active_include_filters})..."
            )
            return True

        # Check exclusion filters - skip if job title matches any exclude filter
        if active_exclude_filters and any(
            keyword.lower() in job_title.lower() for keyword in active_exclude_filters
        ):
            self.logger.debug(
                f"Skipping offer '{job_title}' (matches exclude filters: {active_exclude_filters})..."
            )
            return True

        return False

    async def filter_already_scraped_offers(  # noqa: C901
        self, notion_client: NotionClient
    ) -> None:
        """
        Check if offers already exist in the Notion database and remove existing ones from self._offers_urls.

        This method extracts all IDs from self._offers_urls, queries Notion in batch to check which ones
        already exist, and then removes the existing offers from the list.

        Args:
            notion_client (NotionClient): The Notion client to use for checking existence.
        """
        if not self._offers_urls:
            self.logger.debug("No offers to filter - _offers_urls is empty")
            return

        # Extract all IDs from the offers_urls list, filtering out None values
        offer_ids = []
        for offer_dict in self._offers_urls:
            offer_id = offer_dict.get("id")
            if offer_id is not None and isinstance(offer_id, str):
                offer_ids.append(offer_id)

        if not offer_ids:
            self.logger.debug("No valid offer IDs found in _offers_urls")
            return

        self.logger.debug(
            f"Checking {len(offer_ids)} offers against Notion database..."
        )

        # Use NotionClient's batch checking method
        existence_results = notion_client._check_multiple_offers_exist(offer_ids)

        # Filter out existing offers from self._offers_urls
        initial_count = len(self._offers_urls)
        filtered_offers = []
        for offer_dict in self._offers_urls:
            offer_id = offer_dict.get("id")
            # Keep offer if ID is None/invalid or if it doesn't exist in Notion
            if (
                offer_id is None
                or not isinstance(offer_id, str)
                or not existence_results.get(offer_id, False)
            ):
                filtered_offers.append(offer_dict)

        self._offers_urls = filtered_offers

        filtered_count = initial_count - len(self._offers_urls)
        if self.debug or filtered_count > 0:
            self.logger.info(
                f"Filtered out {filtered_count} existing offers. {len(self._offers_urls)} offers remaining."
            )

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
                self.logger.debug(f"Problematic offer input: {offer_input}")
            return None

    async def save_error_screenshot(self, func_name: str):
        """Save a screenshot with the function name and timestamp."""
        if self._page:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"error_{func_name}_{timestamp}.png"
            path = os.path.join("screenshots", filename)
            os.makedirs("screenshots", exist_ok=True)
            await self._page.screenshot(path=path)
            self.logger.info(f"Saved error screenshot: {path}")
        else:
            self.logger.warning("No page available for screenshot.")

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
                self.logger.debug(f"Failed to click {locator}: {e}")
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
                self.logger.debug(f"Failed to get text from selector {selector}: {e}")
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
                self.logger.debug(f"Failed to get text from locator: {e}")
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
                self.logger.debug(
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
            await self.filter_already_scraped_offers(self.notion_client)
            raw_offers = await self.parse_offers()

            validated_offers = []
            for offer_input in raw_offers:
                job_offer = self.convert_to_job_offer(offer_input)
                if job_offer:
                    validated_offers.append(job_offer)

            self.logger.info(
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
