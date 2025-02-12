import os
import time
from typing import Any, Dict

from rich.progress import Progress

from src.notion_client import NotionClient
from src.sms_alert import SMSAPI


class OfferProcessor:
    """
    Processes job offers by sending SMS notifications and creating corresponding pages in Notion.

    Attributes:
        notion_client: An instance of NotionClient initialized with the NOTION_API and DATABASE_ID.
        sms_client: An instance of SMSAPI initialized with FREE_MOBILE_USER_ID and FREE_MOBILE_API_KEY.
        total_offers (int): Total number of job offers.
        offers (List[dict]): List containing job offer dictionaries.
    """

    def __init__(self, data: Dict[str, Any]):
        DATABASE_ID = os.getenv("DATABASE_ID")
        NOTION_API = os.getenv("NOTION_API")
        FREE_MOBILE_USER_ID = os.getenv("FREE_MOBILE_USER_ID")
        FREE_MOBILE_API_KEY = os.getenv("FREE_MOBILE_API_KEY")
        assert DATABASE_ID, "DATABASE_ID environment variable is not set."
        assert NOTION_API, "NOTION_API environment variable is not set."
        assert (
            FREE_MOBILE_USER_ID
        ), "FREE_MOBILE_USER_ID environment variable is not set."
        assert (
            FREE_MOBILE_API_KEY
        ), "FREE_MOBILE_API_KEY environment variable is not set."
        self.notion_client = NotionClient(NOTION_API, DATABASE_ID)
        self.sms_client = SMSAPI(FREE_MOBILE_USER_ID, FREE_MOBILE_API_KEY)
        self.total_offers = data.get("total_offers", 0)
        self.offers = data.get("offers", [])

    def process_offer(self, offer, progress, task):
        """
        Process an offer by verifying its existence in the Notion database, sending an SMS alert,
        and creating a new page with the offer details in Notion if it is not a duplicate.

        Parameters:
            offer (dict): Contains the job offer details. Expected keys include:
                - 'Title': The title of the job offer.
                - 'Source': The source of the offer (e.g., "Business France" or others).
                - 'Company': The company offering the job (applicable for "Business France").
                - 'Location': The job location.
                - 'Contract Type': The type of contract.
                - 'Job Type' (optional): The job type (used when Source is not "Business France").
                - 'Job Category' (optional): The job category (used when Source is not "Business France").
                - 'URL' (optional): A URL associated with the offer.
                - 'Description' (optional): A description or additional details, which may be clipped to 2000 characters.
                - Other fields like 'Candidates' or 'Views' (if provided and not 'N/A') are processed as numbers.

            progress: An object for progress tracking, providing:
                - console.log: For logging status messages.
                - advance: A method to advance the progress of the current task.

            task: The current task identifier used by the progress tracker.

        Behavior:
            - Checks if a job with the same title already exists using notion_client.title_exists.
              If it does, logs a skipping message and advances the progress.
            - If the offer is new:
                 - Constructs an SMS message:
                     - For "Business France", includes Title, Company, Location, Contract Type, and Source.
                     - For other sources, includes Title, Job Type, Job Category, Location, Contract Type, and URL.
                 - Sends the SMS via sms_client.send_sms.
                 - Pauses briefly with time.sleep(1).
                 - Builds a dictionary (job_properties) mapping the offer details to the required
                   Notion page property formats (e.g., title, select, number, url, rich_text).
                 - Clipping content to 2000 characters for fields like 'Description' or 'Job Type' when necessary.
                 - Creates a new Notion page with the constructed properties using notion_client.create_page.
        """
        title = offer["Title"]

        if self.notion_client.title_exists(title):
            progress.console.log(
                f"[yellow]Job '{title}' already exists. Skipping...[/yellow]"
            )
            progress.advance(task)
        else:
            if offer["Source"] == "Business France":
                sms_message = (
                    f"New VIE Job Alert!\n"
                    f"Title: {offer['Title']}\n"
                    f"Company: {offer['Company']}\n"
                    f"Location: {offer['Location']}\n"
                    f"Duration: {offer['Duration']}\n"
                )
            else:
                sms_message = (
                    f"CDI Job Alert!\n"
                    f"Title: {offer['Title']}\n"
                    f"Company: {offer['Company']}\n"
                    f"Source: {offer['Source']}\n"
                    f"Location: {offer['Location']}\n"
                    f"Contract Type: {offer['Contract Type']}\n"
                    f"URL: {offer['URL']}\n"
                )
            # self.sms_client.send_sms(sms_message)
            # time.sleep(1)

            job_properties = {
                "Title": {
                    "title": [{"type": "text", "text": {"content": offer["Title"]}}]
                },
                "Source": {"select": {"name": offer["Source"]}},
            }

            for field in offer:
                if field not in ["Title", "Source"] and offer[field] != "N/A":
                    if field in ["Candidates", "Views"]:
                        job_properties[field] = {"number": offer[field]}
                    elif field == "URL":
                        job_properties[field] = {"url": offer[field]}
                    elif field in ["Description", "Job Type"]:
                        content = offer[field]
                        if len(content) > 2000:
                            content = content[:2000]
                            print(
                                f"[yellow]Warning: {field} content clipped to 2000 characters.[/yellow]"
                            )
                        job_properties[field] = {
                            "rich_text": [
                                {"type": "text", "text": {"content": content}}
                            ]
                        }
                    else:
                        job_properties[field] = {"select": {"name": offer[field]}}
            self.notion_client.create_page(job_properties)

    def process_offers(self):
        """
        Processes all job offers, updating a progress bar as each offer is processed.

        The method iterates over the list of offers and processes each one using the
        process_offer method. It uses a Progress context manager to display a progress bar,
        with the total count reflecting the number of offers to process. Any exception raised
        during processing is caught and re-raised as a ValueError with an explanatory message.

        Raises:
            ValueError: If an error occurs during the processing of job offers.
        """
        try:
            with Progress() as progress:
                task = progress.add_task(
                    "Processing job offers...", total=len(self.offers)
                )
                for offer in self.offers:
                    self.process_offer(offer, progress, task)
        except Exception as e:
            raise ValueError(f"Error processing job offers: {e}")
