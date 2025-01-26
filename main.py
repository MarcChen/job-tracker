from doctest import debug
from selenium import webdriver
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


    # Create a single WebDriver instance
    driver = webdriver.Chrome()

    url_vie = "https://mon-vie-via.businessfrance.fr/offres/recherche?query=Data"
    # url = "https://mon-vie-via.businessfrance.fr/offres/recherche?query=Data&specializationsIds=212&missionsTypesIds=1"
    scraper_vie = VIEJobScraper(url_vie, driver=driver)

    url_air_france ="https://recrutement.airfrance.com/offre-de-emploi/liste-offres.aspx"
    scraper_airfrance = AirFranceJobScraper(url = url_air_france, keyword="Data", contract_type="CDI", driver=driver)
    # try :
    #     data = scrapper_bis.scrape()
    #     print(f"Scraped data is : {data}")
    #     # Since the implementation isn't the same as VIE we could filter the offers before scraping on eahc offer, but since it's 
    #     # a company website there's not that much of offers so we can scrape all of them and filter them after
    # finally:
    #     print("Done")
    #     scrapper_bis.close_driver()

    try:
        print("Scraping VIE offers...")
        data_VIE = scraper_vie.scrape()
    finally:
        scraper_vie.close_driver()

    try :
        print("Scraping Air France offers...")
        data_Air_France = scraper_airfrance.scrape()
    finally:
        scraper_airfrance.close_driver()

    data = {
            "total_offers": data_VIE['total_offers'] + data_Air_France['total_offers'],
            "offers": data_VIE + data_Air_France
        }
    print(f"Total offers found: {data['total_offers']}")

    try:
        with Progress() as progress:
            task = progress.add_task("Processing job offers...", total=len(data['offers']))
            for offer in data['offers']:
                title = offer['Title']

                if "data" not in title.strip().lower():
                    progress.console.log(f"[blue]Job '{title}' does not contain 'data'. Skipping...[/blue]")
                    progress.advance(task)
                elif notion_client.title_exists(title):
                    progress.console.log(f"[yellow]Job '{title}' already exists. Skipping...[/yellow]")
                    progress.advance(task)
                else:
                    if offer['Source'] == "Business France":
                        sms_message = (
                            f"New VIE Job Alert!\n"
                            f"Title: {offer['Title']}\n"
                            f"Company: {offer['Company']}\n"
                            f"Location: {offer['Location']}\n"
                            f"Contract Type: {offer['Contract Type']}\n"
                            f"Source: {offer['Source']}\n"
                        )
                    else:
                        sms_message = (
                            f"Air France Job Alert!\n"
                            f"Title: {offer['Title']}\n"
                            f"Job Type: {offer['Job Type']}\n"
                            f"Job Category: {offer['Job Category']}\n"
                            f"Location: {offer['Location']}\n"
                            f"Contract Type: {offer['Contract Type']}\n"
                            f"URL: {offer['URL']}\n"
                        )
                    # sms_client.send_sms(sms_message)
                    # time.sleep(1)

                    job_properties = {
                        "Title": {
                            "title": [
                                {"type": "text", "text": {"content": offer['Title']}}
                            ]
                        },
                        "Source": {"select": {"name": offer['Source']}},
                    }

                    for field in offer:
                        if field not in ['Title', 'Source'] and offer[field] != 'N/A':
                            if field in ['Candidates', 'Views']:
                                job_properties[field] = {"number": offer[field]}
                            elif field == 'URL':
                                job_properties[field] = {"url": offer[field]}
                            elif field in ['Description', 'Job Type']:
                                job_properties[field] = {
                                    "rich_text": [
                                        {"type": "text", "text": {"content": offer[field]}}
                                    ]
                                }
                            else:
                                job_properties[field] = {"select": {"name": offer[field]}}
                    notion_client.create_page(job_properties)
                    progress.console.log(f"[green]Job '{title}' added to Notion and SMS sent![/green]")
                    progress.advance(task)
            
    except Exception as e:
        print(f"Error processing scraped job offers: {e}")
