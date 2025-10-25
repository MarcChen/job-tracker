import logging
import os
import time
from typing import Dict, List, Optional

from rich.progress import Progress

from services.notifications.sms_alert import SMSAPI
from services.scraping.src.airfrance import AirFranceJobScraper
from services.scraping.src.apple import AppleJobScraper
from services.scraping.src.base_model.job_offer import JobOffer, JobSource
from services.scraping.src.config import get_scrapers_config
from services.scraping.src.linked import LinkedInJobScraper
from services.scraping.src.vie import VIEJobScraper
from services.scraping.src.welcome_to_the_jungle import WelcomeToTheJungleJobScraper
from services.storage.src.notion_integration import NotionClient


class OfferProcessor:
    """
    Enhanced processor for job offers using the new Pydantic models and efficient scraping.

    This class handles the complete pipeline from scraping to notification and storage:
    1. Uses scraping infrastructure to get offers from selected sources
    2. Efficiently checks for existing offers using batch operations
    3. Sends SMS notifications for new offers
    4. Creates Notion pages for storage

    Attributes:
        notion_client: An instance of NotionClient for database operations.
        sms_client: An instance of SMSAPI for sending notifications.
        selected_scrapers: List of scraper IDs to use for scraping.
        include_filters: Keywords that must be present in job titles.
        exclude_filters: Keywords that should not be present in job titles.
        debug: Enable debug logging.
    """

    def __init__(
        self,
        notion_client: NotionClient,
        selected_scrapers: Optional[List[str]] = None,
        include_filters: Optional[List[str]] = None,
        exclude_filters: Optional[List[str]] = None,
        debug: bool = False,
    ):
        """
        Initialize the OfferProcessor with scraping configuration.

        Args:
            notion_client: NotionClient instance for database operations
            selected_scrapers: List of scraper IDs to use (defaults to all)
            include_filters: Keywords to include in filtering
            exclude_filters: Keywords to exclude in filtering
            debug: Enable debug mode
        """
        FREE_MOBILE_USER_ID = os.getenv("FREE_MOBILE_USER_ID")
        FREE_MOBILE_API_KEY = os.getenv("FREE_MOBILE_API_KEY")
        assert FREE_MOBILE_USER_ID, (
            "FREE_MOBILE_USER_ID environment variable is not set."
        )
        assert FREE_MOBILE_API_KEY, (
            "FREE_MOBILE_API_KEY environment variable is not set."
        )

        self.notion_client = notion_client
        self.sms_client = SMSAPI(FREE_MOBILE_USER_ID, FREE_MOBILE_API_KEY)
        self.selected_scrapers = selected_scrapers or ["1", "2", "3", "4", "5"]
        self.include_filters = include_filters or []
        self.exclude_filters = exclude_filters or []
        self.debug = debug
        self.logger = logging.getLogger("job-tracker.offer-processor")

        # Will be populated during processing
        self.scraped_offers: List[JobOffer] = []

    def scrape_offers(self) -> List[JobOffer]:  # noqa: C901
        """
        Scrape job offers from selected sources using the configured parameters.

        Returns:
            List of validated JobOffer instances from the scraping process.
        """
        all_offers = []
        scrapers_config = get_scrapers_config()

        if self.debug:
            self.logger.debug(
                f"Starting to scrape from {len(self.selected_scrapers)} selected sources"
            )

        for scraper_id in self.selected_scrapers:
            if scraper_id not in scrapers_config:
                self.logger.warning(
                    f"Warning: Scraper ID {scraper_id} not found in configuration. Skipping."
                )
                continue

            config = scrapers_config[scraper_id]
            if not config.get("enabled", True):
                self.logger.info(f"Scraper {config['name']} is disabled. Skipping.")
                continue

            try:
                # Instantiate the appropriate scraper class based on configuration
                scraper = self._create_scraper(scraper_id, config)

                if self.debug:
                    self.logger.debug(f"Scraping from {config['name']}...")

                # Scrape offers from this source
                offers = scraper.scrape()

                if self.debug:
                    self.logger.debug(
                        f"Found {len(offers)} offers from {config['name']}"
                    )

                all_offers.extend(offers)

            except Exception as e:
                self.logger.error(f"Error scraping from {config['name']}: {e}")
                if self.debug:
                    import traceback

                    traceback.print_exc()
                continue

        self.scraped_offers = all_offers

        if self.debug:
            self.logger.debug(f"Total scraped offers: {len(all_offers)}")

        return all_offers

    def _create_scraper(self, scraper_id: str, config: Dict):
        """
        Create the appropriate scraper instance based on the scraper ID and configuration.

        Args:
            scraper_id: The ID of the scraper to create
            config: The configuration dictionary for this scraper

        Returns:
            An instance of the appropriate scraper class
        """
        # Common parameters for all scrapers
        scraper_params = {
            "url": config["url"],
            "notion_client": self.notion_client,
            "include_filters": self.include_filters,
            "exclude_filters": self.exclude_filters,
            "debug": self.debug,
            "headless": not self.debug,  # Show browser in debug mode
        }

        # Create the appropriate scraper based on ID
        if scraper_id == "1":  # Business France (VIE)
            return VIEJobScraper(**scraper_params)
        elif scraper_id == "2":  # Air France
            scraper_params["keyword"] = config.get("keyword", "")
            scraper_params["contract_type"] = config.get("contract_type", "")
            return AirFranceJobScraper(**scraper_params)
        elif scraper_id == "3":  # Apple
            return AppleJobScraper(**scraper_params)
        elif scraper_id in {"4", "5"}:  # Welcome to the Jungle (Data Engineer or AI)
            # Use config values, defaults are always present in config
            scraper_params["keyword"] = config["keyword"]
            scraper_params["location"] = config["location"]
            return WelcomeToTheJungleJobScraper(**scraper_params)
        elif scraper_id in {"6", "7"}:  # LinkedIn
            scraper_params["keyword"] = config.get("keyword", "data")
            scraper_params["location"] = config.get("location", "Paris")

            return LinkedInJobScraper(**scraper_params)
        else:
            raise ValueError(f"Unknown scraper ID: {scraper_id}")

    def process_offers(self, offers: Optional[List[JobOffer]] = None) -> None:
        """
        Process job offers by checking existence, sending notifications, and creating Notion pages.

        Args:
            offers: Optional list of JobOffer instances to process.
                   If None, will use scraped_offers from scrape_offers().
        """
        # TODO: Refactor to use Python generators (yield) for processing offers to optimize memory usage

        # Use provided offers or fall back to scraped offers
        offers_to_process = offers or self.scraped_offers

        if not offers_to_process:
            self.logger.warning(
                "No offers to process. Run scrape_offers() first or provide offers."
            )
            return

        try:
            # Batch check which offers already exist for efficiency
            self.logger.info(
                f"Checking {len(offers_to_process)} offers for duplicates..."
            )
            existence_result = self.notion_client.offer_exists(offers_to_process)

            # Handle the case where result is either bool or dict
            if isinstance(existence_result, dict):
                existence_map = existence_result
            else:
                # Single offer case - create a simple map
                existence_map = (
                    {offers_to_process[0].offer_id: existence_result}
                    if offers_to_process
                    else {}
                )

            new_offers = [
                offer
                for offer in offers_to_process
                if not existence_map.get(offer.offer_id, False)
            ]
            self.logger.info(f"Found {len(new_offers)} new offers to process")

            with Progress() as progress:
                task = progress.add_task(
                    "Processing job offers...", total=len(offers_to_process)
                )
                for offer in offers_to_process:
                    # Check if offer already exists using pre-computed existence map
                    if existence_map.get(offer.offer_id, False):
                        progress.console.log(
                            f"[yellow]Job '{offer.title}' (ID: {offer.offer_id}) already exists. Skipping...[/yellow]"
                        )
                        progress.advance(task)
                    else:
                        self._process_new_offer(offer, progress, task)

        except Exception as e:
            raise ValueError(f"Error processing job offers: {e}")

    def scrape_and_process(self) -> List[JobOffer]:
        """
        Complete workflow: scrape offers from selected sources and process them.

        Returns:
            List of scraped JobOffer instances.
        """
        # Scrape offers
        scraped = self.scrape_offers()

        # Process the scraped offers
        if scraped:
            self.process_offers(scraped)

        return scraped

    def _process_new_offer(self, offer: JobOffer, progress, task):
        """Process a new offer that doesn't exist in the database."""
        if offer.source not in [JobSource.LINKEDIN, JobSource.WELCOME_TO_THE_JUNGLE]:
            sms_message = (
                f"New offer from {offer.source}\n"
                f"Title: {offer.title}\n"
                f"Company: {offer.company}\n"
                f"Location: {offer.location}\n"
                if offer.location
                else f"Duration: {offer.duration}\n"
                if offer.duration
                else ""
            )
            self.sms_client.send_sms(sms_message)
            time.sleep(5)

        # Use the JobOffer's built-in Notion format conversion
        result = self.notion_client.create_page_from_job_offer(offer)
        if result:
            progress.console.log(
                f"[green]Created page for '{offer.title}' (ID: {offer.offer_id})[/green]"
            )
        else:
            progress.console.log(
                f"[red]Failed to create page for '{offer.title}' (ID: {offer.offer_id})[/red]"
            )

        progress.advance(task)
