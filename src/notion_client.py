import json
from typing import Dict, List, Optional

import requests


class NotionClient:
    def __init__(self, notion_api_key: str, database_id: str):
        """
        Initialize the NotionClient with API key, database ID, and project root.

        Args:
            notion_api_key (str): Notion API key.
            database_id (str): Notion database ID.
        """
        self.notion_api_key = notion_api_key
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {self.notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    def title_exists(self, title: str) -> bool:
        """
        Checks if a page with the given title already exists in the database.

        Args:
            title (str): The title to check.

        Returns:
            bool: True if the title exists, False otherwise.
        """
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        try:
            response = requests.post(url, headers=self.headers, json={})
            response.raise_for_status()
            data = response.json()
            titles = [
                page["properties"]["Title"]["title"][0]["text"]["content"]
                for page in data.get("results", [])
                if "Title" in page["properties"]
                and page["properties"]["Title"]["title"]
            ]
            return title in titles
        except requests.exceptions.RequestException as e:
            print(f"Error checking if title exists: {e}")
            return False

    def create_page(self, properties: Dict) -> Optional[Dict]:
        """
        Creates a new page in the specified Notion database if the title does not already exist.

        Args:
            properties (Dict): A dictionary containing the properties for the new page.

        Returns:
            Optional[Dict]: The JSON response from the Notion API if successful; None otherwise.
        """
        title = (
            properties.get("Title", {})
            .get("title", [{}])[0]
            .get("text", {})
            .get("content", "")
        )
        if not title:
            print("Error: Title property is required to create a page.")
            return None

        if self.title_exists(title):
            print(
                f"Page with title '{title}' already exists. Skipping creation."
            )
            return None

        # Convert payload to match Notion database schema
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
        }

        url = "https://api.notion.com/v1/pages"

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            print(f"Page '{title}' created successfully!")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating page '{title}': {e}")
            print(
                f"Response Content: {response.text if 'response' in locals() else 'No response'}"
            )
            print(f"Payload: {json.dumps(payload, indent=2)}")
            return None

    def get_page_titles(self) -> List[str]:
        """
        Retrieves the titles of all pages in the specified Notion database.

        Returns:
            List[str]: A list of titles of all pages in the database.
        """
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        try:
            response = requests.post(url, headers=self.headers, json={})
            response.raise_for_status()
            data = response.json()
            titles = [
                page["properties"]["Title"]["title"][0]["text"]["content"]
                for page in data.get("results", [])
                if "Title" in page["properties"]
                and page["properties"]["Title"]["title"]
            ]
            return titles
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page titles: {e}")
            return []
