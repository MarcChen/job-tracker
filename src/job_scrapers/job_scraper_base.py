from typing import Dict, List, Union
import warnings
from selenium import webdriver

class JobScraperBase:
    def __init__(
        self,
        url: str,
        driver: webdriver.Chrome = None,
        include_filters: List[str] = None,
        exclude_filters: List[str] = None,
    ):
        """
        Initialize the JobScraperBase class.

        Args:
            url (str): The URL of the job listing page to scrape.
        """
        self.url = url
        self.driver = setup_driver() if None else driver

    def _init_offer_dict(self) -> Dict[str, Union[str, int]]:
        """Initialize a standardized offer dictionary with default values."""
        return {
            "Title": "N/A",
            "Company": "N/A",
            "Location": "N/A",
            "Contract Type": "N/A",
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

    def load_all_offers(self) -> None:
        """
        Load all offers by repeatedly clicking 'Voir Plus d'Offres' with added randomness.
        """
        raise NotImplementedError(
            "This method should be implemented by subclasses"
        )

    def extract_offers(self) -> List[Dict[str, Union[str, int]]]:
        """
        Extract offers data from the loaded page.

        Returns:
            List[Dict[str, Union[str, int]]]: A list of dictionaries containing offer details.
        """
        raise NotImplementedError(
            "This method should be implemented by subclasses"
        )

    def extract_total_offers(self) -> Union[str, int]:
        """
        Extract the total offers count displayed on the page.

        Returns:
            Union[str, int]: The total offers count as an integer, or 'Unknown' if an error occurs.
        """
        raise NotImplementedError(
            "This method should be implemented by subclasses"
        )

    def scrape(
        self,
    ) -> Dict[str, Union[str, List[Dict[str, Union[str, int]]]]]:
        """
        Main method to perform the scraping.

        Returns:
            Dict[str, Union[str, List[Dict[str, Union[str, int]]]]]: A dictionary containing the total offers count and offers data.
        """
        self.load_all_offers()
        raw_offers = self.extract_offers()
        validated_offers = [
            offer for offer in raw_offers if self.validate_offer(offer)
        ]
        return {
            "total_offers": self.extract_total_offers(),
            "offers": validated_offers,
        }