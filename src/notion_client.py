import requests
import os
from rich import print
import json
from typing import Dict, List, Optional, Set

class NotionClient:
    def __init__(self, notion_api_key: str, database_id: str, project_root: str):
        """
        Initialize the NotionClient with API key, database ID, and project root.

        Args:
            notion_api_key (str): Notion API key.
            database_id (str): Notion database ID.
            project_root (str): Path to the project root directory.
        """
        self.notion_api_key = notion_api_key
        self.database_id = database_id
        self.project_root = project_root
        self.headers = {
            "Authorization": f"Bearer {self.notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def get_filtered_sorted_database(self) -> Optional[Dict]:
        """
        Fetches the database information from Notion with specified filters and sorting.

        Returns:
            Optional[Dict]: The JSON response from the Notion API if the request is successful; None otherwise.
        """
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        
        try:
            with open(f"{self.project_root}/services/notion/config/query_payload.json", 'r') as file: 
                query_payload = json.load(file)

            response = requests.post(url, headers=self.headers, json=query_payload)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error fetching database: {e}")
            return None
        except FileNotFoundError as e:
            print(f"Error loading query payload: {e}")
            return None

    def fetch_parent_page_names(self, parent_page_ids: Set[str]) -> Dict[str, Optional[str]]:
        """
        Fetches names of multiple parent pages in one batch to minimize API calls.

        Args:
            parent_page_ids (Set[str]): A set of unique parent page IDs (without hyphens).

        Returns:
            Dict[str, Optional[str]]: A dictionary mapping parent page IDs to their names.
        """
        parent_page_names: Dict[str, Optional[str]] = {}
        for page_id in parent_page_ids:
            page_id = page_id.replace("-", "")
            url = f"https://api.notion.com/v1/pages/{page_id}"

            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                title_property = data.get("properties", {}).get("Name", {}).get("title", None)
                if title_property and len(title_property) > 0:
                    parent_page_names[page_id] = title_property[0].get("text", {}).get("content", None)
                else:
                    parent_page_names[page_id] = None

            except requests.exceptions.RequestException as e:
                print(f"Error fetching parent page {page_id}: {e}")
                parent_page_names[page_id] = None

        return parent_page_names

    def mark_page_as_completed(self, page_id: str) -> Optional[Dict]:
        """
        Marks the 'Status' property of a Notion page as 'Done'.

        Args:
            page_id (str): The ID of the Notion page to update.

        Returns:
            Optional[Dict]: The JSON response from the Notion API if successful; None otherwise.
        """
        url = f"https://api.notion.com/v1/pages/{page_id}"
        payload = {
            "properties": {
                "Status": {
                    "status": {
                        "name": "Done"
                    }
                }
            }
        }

        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            if response.status_code == 200:
                print(f"Page {page_id} marked as 'Done' successfully!")
                return response.json()
            else:
                print(f"Failed to mark page {page_id} as 'Done'. Status Code: {response.status_code}. Error: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error marking page {page_id} as 'Done': {e}")
            return None

    def create_new_page(self, title: str) -> Optional[Dict]:
        """
        Create a new page in the Notion database with the "Today" checkbox set to True.

        Args:
            title (str): The title of the new page.

        Returns:
            Optional[Dict]: The JSON response from the Notion API if successful; None otherwise.
        """
        url = "https://api.notion.com/v1/pages"
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Name": {
                    "title": [
                        {"text": {"content": title}}
                    ]
                },
                "Today": {
                    "checkbox": True
                }
            }
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            print(f"Page '{title}' created successfully with 'Today' checkbox set to True!")
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error creating page '{title}': {e}")
            return None

    def parse_notion_response(self, response: Dict) -> List[Dict]:
        """
        Parse the Notion response to extract relevant fields, including parent page names.

        Args:
            response (Dict): The JSON response from Notion API.

        Returns:
            List[Dict]: A list of dictionaries containing extracted fields with None instead of [] or {}.
        """
        try:
            results = response.get('results', [])
            parsed_data: List[Dict] = []

            for page in results:
                properties = page.get('properties', {})
                page_id = page.get('id', None).replace("-", "")

                tag = properties.get('Tags', {}).get('multi_select', None)
                if tag and len(tag) > 0:
                    tag = tag[0].get('name', None)
                else:
                    tag = None

                importance_property = properties.get('Importance', {}).get('select', None)
                importance = importance_property.get('name', None) if importance_property else None

                unique_id = properties.get('ID', {}).get('unique_id', {}).get('number', None)

                due_date_property = properties.get('Due Date', {}).get('date', None)
                due_date = due_date_property.get('start', None) if due_date_property else None

                page_url = page.get('url', None)

                estimates_property = properties.get('Estimates', {}).get('select', None)
                estimates = estimates_property.get('name', None) if estimates_property else None

                title = properties.get('Name', {}).get('title', None)
                title_text = title[0]['text']['content'] if title and len(title) > 0 else None

                text_property = properties.get('Text', {}).get('rich_text', None)
                text_property = text_property[0].get('text', {}).get('content', None) if text_property and len(text_property) > 0 else None

                url_property = properties.get('URL', {}).get('rich_text', None)
                links = [
                    text.get('text', {}).get('link', {}).get('url', None)
                    for text in (url_property or [])
                    if text.get('text', {}).get('link')
                ] if url_property else None
                links = links if links and len(links) > 0 else None

                laste_edited_time = page.get('last_edited_time', None)
                created_time = page.get('created_time', None)

                parent_page_id = properties.get('Parent item', {}).get('relation', None)
                if parent_page_id and len(parent_page_id) > 0:
                    parent_page_id = parent_page_id[0].get('id', "").replace("-", "")
                else:
                    parent_page_id = None

                parsed_data.append({
                    "unique_id": unique_id,
                    "page_id": page_id,
                    "title": title_text,
                    "created_time": created_time,
                    "last_edited_time": laste_edited_time,
                    "estimates": estimates,
                    "importance": importance,
                    "tags": tag,
                    "due_date": due_date,
                    "page_url": page_url,
                    "text": text_property,
                    "url": links,
                    "parent_page_id": parent_page_id
                })

            parent_page_ids: Set[str] = {item['parent_page_id'] for item in parsed_data if item['parent_page_id']}
            parent_page_names = self.fetch_parent_page_names(parent_page_ids)

            for item in parsed_data:
                if item['parent_page_id']:
                    item['parent_page_name'] = parent_page_names.get(item['parent_page_id'], None)
                else:
                    item['parent_page_name'] = None

            return parsed_data

        except KeyError as e:
            print(f"Error parsing Notion response: Missing key {e}")
            return []
        except Exception as e:
            print(f"Unexpected error while parsing Notion response: {e}")
            return []