from typing import Dict, List, Optional
from notion_client import Client


class NotionClient:
    def __init__(self, notion_api_key: str, database_id: str):
        """
        Initialize the NotionClient with API key and database ID using the official Notion integration.

        Args:
            notion_api_key (str): Notion API key.
            database_id (str): Notion database ID.
        """
        self.database_id = database_id
        self.client = Client(auth=notion_api_key)
        self.all_offers = self.get_all_offers()

    def offer_exists(self, title: str, source: str, company: Optional[str] = None) -> bool:
        """
        Checks if an offer with the given properties already exists in the loaded offers.

        Args:
            title (str): Title of the offer.
            source (str): Source of the offer.
            company (Optional[str]): Company of the offer.
            url (Optional[str]): URL of the offer.

        Returns:
            bool: True if the offer exists, False otherwise.
        """
        for offer in self.all_offers:
            if (
                offer.get("Title", "").lower() == title.lower() and
                offer.get("Source", "").lower() == source.lower() and
                (not company or offer.get("Company", "").lower() == company.lower())
            ):
                return True
        return False

    def create_page(self, properties: Dict) -> Optional[Dict]:
        """
        Creates a new page in the specified Notion database if the title does not already exist.

        Args:
            properties (Dict): A dictionary containing the properties for the new page.

        Returns:
            Optional[Dict]: The JSON response from the Notion API if successful; None otherwise.
        """
        title = self._extract_title(properties)
        company = self._extract_select(properties, "Company")
        source = self._extract_select(properties, "Source")
        if not title:
            print("Error: Title property is required to create a page.")
            return None
        if self.offer_exists(title, source, company=company):
            print(f"Offer with title '{title}' already exists. Skipping creation.")
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

    def get_all_offers(self) -> List[Dict]:
        """
        Retrieves all offers from the Notion database, returning a list of dictionaries
        with each offer's properties: 'Title', 'Company', 'Location', 'Source', and 'URL'.

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
                self._extract_select(properties, "Company").strip().lower()
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
    notion_client.delete_duplicate_offers()
