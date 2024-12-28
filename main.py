from src.selenium_script import JobScraper
from src.notion_client import NotionClient
from src.sms_alert import SMSAPI
from rich.progress import Progress
import os

if __name__ == "__main__":
    DATABASE_ID = os.getenv("DATABASE_ID")
    NOTION_API = os.getenv("NOTION_API")
    FREE_MOBILE_USER_ID = os.getenv("FREE_MOBILE_USER_ID")
    FREE_MOBILE_API_KEY = os.getenv("FREE_MOBILE_API_KEY")

    assert DATABASE_ID, "DATABASE_ID environment variable is not set."
    assert NOTION_API, "NOTION_API environment variable is not set."
    assert FREE_MOBILE_USER_ID, "FREE_MOBILE_USER_ID environment variable is not set."
    assert FREE_MOBILE_API_KEY, "FREE_MOBILE_API_KEY environment variable is not set."

    notion_client = NotionClient(NOTION_API, DATABASE_ID)
    sms_client = SMSAPI(FREE_MOBILE_USER_ID, FREE_MOBILE_API_KEY)

    url = "https://mon-vie-via.businessfrance.fr/offres/recherche?query=&specializationsIds=212&specializationsIds=24&missionsTypesIds=1&gerographicZones=4"
    scraper = JobScraper(url)

    try:
        print("Scraping job offers...")
        data = scraper.scrape()
        print(f"Total offers found: {data['total_offers']}")

        with Progress() as progress:
            task = progress.add_task("Processing job offers...", total=len(data['offers']))

            for offer in data['offers']:
                title = offer['Title']

                if notion_client.title_exists(title):
                    progress.console.log(f"[yellow]Job '{title}' already exists. Skipping...[/yellow]")
                else:
                    sms_message = (
                        f"New Job Alert!\n"
                        f"Title: {offer['Title']}\n"
                        f"Company: {offer['Company']}\n"
                        f"Location: {offer['Location']}\n"
                        f"Contract Type: {offer['Contract Type']}\n"
                        f"Duration: {offer['Duration']}\n"
                        f"Views: {offer['Views']}\n"
                        f"Candidates: {offer['Candidates']}\n"
                    )
                    sms_client.send_sms(sms_message)

                    job_properties = {
                        "Title": {
                            "title": [
                                {"type": "text", "text": {"content": offer['Title']}}
                            ]
                        },
                        "Candidates": {"number": offer['Candidates']},
                        "Views": {"number": offer['Views']},
                        "ContractType": {"select": {"name": offer['Contract Type']}},
                        "Company": {"select": {"name": offer['Company']}},
                        "Location": {"select": {"name": offer['Location']}},
                        "Duration": {"select": {"name": offer['Duration']}},
                    }
                    notion_client.create_page(job_properties)
                    progress.console.log(f"[green]Job '{title}' added to Notion and SMS sent![/green]")

                progress.advance(task)
            

    finally:
        scraper.close_driver()
