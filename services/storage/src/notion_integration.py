from typing import Dict, List, Optional, Union

from notion_client import Client

from services.scraping.src.base_model.job_offer import JobOffer


class NotionClient:
    def __init__(self, notion_api_key: str, database_id: str):
        """
        Initialize the NotionClient with API key and database ID using the official Notion integration.

        Args:
            notion_api_key (str): Notion API key.
            database_id (str): Notion database ID.

        Raises:
            ValueError: If either notion_api_key or database_id is empty or None.
        """
        if not notion_api_key or not database_id:
            raise ValueError(
                "Both notion_api_key and database_id must be provided and non-empty"
            )

        self.database_id = database_id
        self.client = Client(auth=notion_api_key)

    def offer_exists(
        self, job_offers: Union[JobOffer, List[JobOffer]]
    ) -> Union[bool, Dict[str, bool]]:
        """
        Checks if job offer(s) already exist in the Notion database based on their offer ID.

        Args:
            job_offers: A single JobOffer instance or list of JobOffer instances to check.

        Returns:
            If single JobOffer: bool indicating if the offer exists.
            If list of JobOffers: Dict mapping offer_id to bool indicating existence.
        """
        # Handle single JobOffer
        if isinstance(job_offers, JobOffer):
            return self._check_single_offer_exists(job_offers.offer_id)

        # Handle list of JobOffers - batch query
        if not job_offers:
            return {}

        offer_ids = [offer.offer_id for offer in job_offers]
        return self._check_multiple_offers_exist(offer_ids)

    def _check_single_offer_exists(self, offer_id: str) -> bool:
        """
        Check if a single offer exists by querying the database for the offer ID.

        Args:
            offer_id: The 5-digit offer ID to search for.

        Returns:
            bool: True if the offer exists, False otherwise.
        """
        try:
            query = {
                "database_id": self.database_id,
                "filter": {"property": "Offer ID", "rich_text": {"equals": offer_id}},
            }
            response = self.client.databases.query(**query)
            return len(response.get("results", [])) > 0
        except Exception as e:
            print(f"Error checking if offer {offer_id} exists: {e}")
            return False

    def _check_multiple_offers_exist(self, offer_ids: List[str]) -> Dict[str, bool]:
        """
        Check if multiple offers exist by querying the database with a filter for all offer IDs.

        Args:
            offer_ids: List of 5-digit offer IDs to search for.

        Returns:
            Dict mapping offer_id to bool indicating existence.
        """
        result = {offer_id: False for offer_id in offer_ids}

        if not offer_ids:
            return result

        try:
            # Build OR filter for all offer IDs
            if len(offer_ids) == 1:
                # Single offer ID - use simple filter
                filter_condition = {
                    "property": "Offer ID",
                    "rich_text": {"equals": offer_ids[0]},
                }
            else:
                # Multiple offer IDs - use OR filter
                filter_condition = {
                    "or": [
                        {"property": "Offer ID", "rich_text": {"equals": offer_id}}
                        for offer_id in offer_ids
                    ]
                }

            query = {"database_id": self.database_id, "filter": filter_condition}

            # Get all pages that match any of the offer IDs
            response = self.client.databases.query(**query)

            # Extract existing offer IDs from results
            existing_ids = set()
            for page in response.get("results", []):
                properties = page.get("properties", {})
                existing_offer_id = self._extract_offer_id(properties)
                if existing_offer_id:
                    existing_ids.add(existing_offer_id)

            # Check which of our offer IDs exist
            for offer_id in offer_ids:
                result[offer_id] = offer_id in existing_ids

        except Exception as e:
            print(f"Error checking multiple offers existence: {e}")

        return result

    def create_page(
        self, properties: Dict, job_offer: Optional[JobOffer] = None
    ) -> Optional[Dict]:
        """
        Creates a new page in the specified Notion database if the offer does not already exist.

        Args:
            properties (Dict): A dictionary containing the properties for the new page.
            job_offer (Optional[JobOffer]): JobOffer instance to check for existence.
                                          If not provided, will create page without checking.

        Returns:
            Optional[Dict]: The JSON response from the Notion API if successful; None otherwise.
        """
        title = self._extract_title(properties)
        if not title:
            print("Error: Title property is required to create a page.")
            return None

        # Check if offer exists only if JobOffer is provided
        if job_offer and self.offer_exists(job_offer):
            print(
                f"Offer with ID '{job_offer.offer_id}' already exists. Skipping creation."
            )
            return None

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
        }
        try:
            result = self.client.pages.create(**payload)
            print(f"Page '{title}' created successfully!")
            return result
        except Exception as e:
            print(f"Error creating page '{title}': {e}")
            print(f"Payload: {payload}")
            return None

    def create_page_from_job_offer(self, job_offer: JobOffer) -> Optional[Dict]:
        """
        Creates a new page in the Notion database from a JobOffer instance.

        Args:
            job_offer (JobOffer): The JobOffer instance to create a page for.

        Returns:
            Optional[Dict]: The JSON response from the Notion API if successful; None otherwise.
        """
        properties = job_offer.to_notion_format()
        return self.create_page(properties, job_offer)

    def create_pages_from_job_offers(
        self, job_offers: List[JobOffer]
    ) -> List[Optional[Dict]]:
        """
        Creates multiple pages in the Notion database from a list of JobOffer instances.
        Uses batch checking to efficiently determine which offers already exist.

        Args:
            job_offers (List[JobOffer]): List of JobOffer instances to create pages for.

        Returns:
            List[Optional[Dict]]: List of results from the Notion API for each offer.
        """
        if not job_offers:
            return []

        # Batch check which offers already exist
        existence_result = self.offer_exists(job_offers)

        results = []
        for job_offer in job_offers:
            # existence_result is a Dict[str, bool] when checking multiple offers
            if isinstance(existence_result, dict) and existence_result.get(
                job_offer.offer_id, False
            ):
                print(
                    f"Offer with ID '{job_offer.offer_id}' already exists. Skipping creation."
                )
                results.append(None)
            else:
                properties = job_offer.to_notion_format()
                result = self.create_page(
                    properties, None
                )  # Skip existence check since we already did it
                results.append(result)

        return results

    def _fetch_all_results(self, query: Dict) -> List[dict]:
        """
        Helper method to retrieve all unique results from the Notion database while handling pagination.
        """
        results = []
        seen_ids = set()
        start_cursor = None
        while True:
            params = query.copy()
            if start_cursor:
                params["start_cursor"] = start_cursor
            response = self.client.databases.query(**params)
            for page in response.get("results", []):
                page_id = page.get("id")
                if page_id not in seen_ids:
                    results.append(page)
                    seen_ids.add(page_id)
            if not response.get("has_more", False):
                break
            start_cursor = response.get("next_cursor")
        return results

    def _extract_title(self, properties: dict) -> str:
        """
        Extracts the text content from a title property.
        """
        title_list = properties.get("Title", {}).get("title", [])
        if title_list:
            return title_list[0].get("text", {}).get("content", "")
        return ""

    def _extract_select(self, properties: dict, field_name: str) -> str:
        """
        Extracts the selected value (its name) from a select property.
        """
        field = properties.get(field_name, {}) or {}
        select_data = field.get("select") or {}
        return select_data.get("name", "")

    def _extract_rich_text(self, properties: dict, field_name: str) -> str:
        """
        Extracts the text content from a rich_text property.
        """
        rich_text = properties.get(field_name, {}).get("rich_text", [])
        if rich_text:
            return rich_text[0].get("text", {}).get("content", "")
        return ""

    def _extract_url(self, properties: dict, field_name: str) -> str:
        """
        Extracts the URL from a URL property.
        """
        url = properties.get(field_name, {}).get("url", "")
        return url if url else ""

    def _extract_offer_id(self, properties: dict) -> str:
        """
        Extracts the offer ID from a rich_text property.
        """
        return self._extract_rich_text(properties, "Offer ID")

    def get_all_offers(self) -> List[Dict]:
        """
        Retrieves all offers from the Notion database, returning a list of dictionaries
        with each offer's properties including the Offer ID.

        Returns:
            List[dict]: A list of dictionaries with offer properties.
        """
        query = {"database_id": self.database_id}
        pages = self._fetch_all_results(query)

        offers = []
        for page in pages:
            properties = page.get("properties", {})
            offer = {
                "Title": self._extract_title(properties),
                "Company": self._extract_select(properties, "Company"),
                "Location": self._extract_select(properties, "Location"),
                "Source": self._extract_select(properties, "Source"),
                "URL": self._extract_url(properties, "URL"),
                "Offer ID": self._extract_offer_id(properties),
            }
            offers.append(offer)
        return offers

    def delete_duplicate_offers(self):
        """
        Deletes duplicate Notion pages based on offer properties, keeping the first occurrence.
        Retrieves pages using _fetch_all_results and archives duplicates by making a REST API call.
        """
        query = {"database_id": self.database_id}
        pages = self._fetch_all_results(query)
        seen_offers = {}
        duplicates = []

        for page in pages:
            properties = page.get("properties", {})
            key = (
                self._extract_title(properties).strip().lower(),
                self._extract_select(properties, "Source").strip().lower(),
                self._extract_select(properties, "Company").strip().lower(),
            )
            if key in seen_offers:
                duplicates.append(page)
            else:
                seen_offers[key] = page

        for dup in duplicates:
            page_id = dup.get("id")
            try:
                self.client.pages.update(page_id, archived=True)
                print(f"Deleted duplicate page {page_id}")
            except Exception as e:
                print(f"Error deleting page {page_id}: {e}")


if __name__ == "__main__":
    # Cleaning up duplicate offers in the Notion database
    import os

    DATABASE_ID = os.getenv("DATABASE_ID")
    NOTION_API = os.getenv("NOTION_API")
    assert DATABASE_ID, "DATABASE_ID environment variable is not set."
    assert NOTION_API, "NOTION_API environment variable is not set."
    notion_client = NotionClient(NOTION_API, DATABASE_ID)
    # notion_client.delete_duplicate_offers()
