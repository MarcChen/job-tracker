from src.selenium_script import VIEJobScraper, AirFranceJobScraper
from src.notion_client import NotionClient
from src.sms_alert import SMSAPI
from rich.progress import Progress
import os
import time

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

    # url = "https://mon-vie-via.businessfrance.fr/offres/recherche?query=Data"
    # scraper = VIEJobScraper(url)

    url ="https://recrutement.airfrance.com/offre-de-emploi/liste-offres.aspx"
    scrapper_bis = AirFranceJobScraper(url = url, keyword="Data", contract_type="CDI")
    scrapper_bis.load_all_offers()

    # try:
    #     print("Scraping job offers...")
    #     data = scraper.scrape()
    #     print(f"Total offers found: {data['total_offers']}")

    #     with Progress() as progress:
    #         task = progress.add_task("Processing job offers...", total=len(data['offers']), start=False)
    #         progress.start_task(task)

    #         for offer in data['offers']:
    #             title = offer['Title']

    #             if "data" not in title.strip().lower():
    #                 progress.console.log(f"[blue]Job '{title}' does not contain 'data'. Skipping...[/blue]")
    #                 progress.advance(task)
    #                 continue
    #             if notion_client.title_exists(title):
    #                 progress.console.log(f"[yellow]Job '{title}' already exists. Skipping...[/yellow]")
    #                 progress.advance(task)
    #             else:
    #                 sms_message = (
    #                     f"New Job Alert!\n"
    #                     f"Title: {offer['Title']}\n"
    #                     f"Company: {offer['Company']}\n"
    #                     f"Location: {offer['Location']}\n"
    #                     f"Contract Type: {offer['Contract Type']}\n"
    #                     f"Duration: {offer['Duration']}\n"
    #                     f"Views: {offer['Views']}\n"
    #                     f"Candidates: {offer['Candidates']}\n"
    #                 )
    #                 sms_client.send_sms(sms_message)
    #                 time.sleep(1)

    #                 job_properties = {
    #                     "Title": {
    #                         "title": [
    #                             {"type": "text", "text": {"content": offer['Title']}}
    #                         ]
    #                     },
    #                     "Candidates": {"number": offer['Candidates']},
    #                     "Views": {"number": offer['Views']},
    #                     "ContractType": {"select": {"name": offer['Contract Type']}},
    #                     "Company": {"select": {"name": offer['Company']}},
    #                     "Location": {"select": {"name": offer['Location']}},
    #                     "Duration": {"select": {"name": offer['Duration']}},
    #                 }
    #                 notion_client.create_page(job_properties)
    #                 progress.console.log(f"[green]Job '{title}' added to Notion and SMS sent![/green]")

    #             progress.advance(task)
            

    # finally:
    #     scraper.close_driver()
