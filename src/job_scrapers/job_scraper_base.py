import warnings
from typing import Dict, List, Union

from selenium import webdriver


class JobScraperBase:
    def __init__(
        self,
        url: str,
        driver: webdriver.Chrome = None,
        include_filters: List[str] = None,
        exclude_filters: List[str] = None,
        debug: bool = False,
    ):
        """
        Initialize the JobScraperBase class.

        Args:
            url (str): The URL of the job listing page to scrape.
        """
        self.url = url
        self.driver = driver
        self.include_filters = include_filters
        self.exclude_filters = exclude_filters

    def _init_offer_dict(self) -> Dict[str, Union[str, int]]:
        """Initialize a standardized offer dictionary with default values."""
        return {
            "Title": "N/A",
            "Company": "N/A",
            "Location": "N/A",
            "Contract Type": "N/A",
            "Experience Level": "N/A",
            "Salary": "N/A",
            "Duration": "N/A",
            "Views": "N/A",
            "Candidates": "N/A",
            "Source": "N/A",
            "URL": "N/A",
            "Reference": "N/A",
            "Job Category": "N/A",
            "Job Type": "N/A",
            "Schedule Type": "N/A",
            "Description": "N/A",
        }

    def validate_offer(self, offer: dict) -> bool:
        """Ensure required fields are present."""
        required_fields = ["Title", "Company", "Location", "Source"]
        missing_fields = [field for field in required_fields if offer[field] == "N/A"]
        if missing_fields:
            warnings.warn("Offer missing fields {}: {}".format(missing_fields, offer))
            return False
        return True

    def should_skip_offer(self, job_title: str) -> bool:
        """
        Determine if an offer should be skipped based on include/exclude filters.
        """
        if self.include_filters and not any(
            keyword.lower() in job_title.lower() for keyword in self.include_filters
        ):
            print(f"Skipping offer '{job_title}' ...")
            return True
        if self.exclude_filters and any(
            keyword.lower() in job_title.lower() for keyword in self.exclude_filters
        ):
            print(f"Skipping offer '{job_title}' ...")
            return True
        return False

    def load_all_offers(self) -> None:
        """
        Load all offers by repeatedly clicking 'Voir Plus d'Offres' with added randomness.
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    def extract_offers(self) -> List[Dict[str, Union[str, int]]]:
        """
        Extract offers data from the loaded page.

        Returns:
            List[Dict[str, Union[str, int]]]: A list of dictionaries containing offer details.
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    def scrape(self) -> List[Dict[str, Union[str, int]]]:
        """
        Perform the scraping process.

        This method loads all offers, extracts the raw offers data, validates each offer,
        and returns a list of validated job offers.

        Returns:
            List[Dict[str, Union[str, int]]]: A list of dictionaries, each representing a validated job offer.
        """
        self.load_all_offers()
        raw_offers = self.extract_offers()
        validated_offers = [offer for offer in raw_offers if self.validate_offer(offer)]
        return validated_offers
