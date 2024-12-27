from src.selenium_script import JobScraper
from src.notion_client import NotionClient
from src.sms_alert import SMSAPI
import os

if __name__ == "__main__":
    DATABASE_ID = os.getenv("DATABASE_ID")
    NOTION_API = os.getenv("NOTION_API")
    FREE_MOBILE_USER_ID=os.getenv("FREE_MOBILE_USER_ID")
    FREE_MOBILE_API_KEY=os.getenv("FREE_MOBILE_API_KEY")


    assert DATABASE_ID, "DATABASE_ID environment variable is not set."
    assert NOTION_API, "NOTION_API environment variable is not set."
    assert FREE_MOBILE_USER_ID, "FREE_MOBILE_USER_ID environment variable is not set."
    assert FREE_MOBILE_API_KEY, "FREE_MOBILE_API_KEY environment variable is not set."

    client = NotionClient(NOTION_API, DATABASE_ID)

    # Create a new page
    new_page_properties = {
        "Title": {
            "title": [
                {"type": "text", "text": {"content": "Sample Random Page"}}
            ]
        },
        "Candidates": {"number": 42},
        "Views": {"number": 123},
        "ContractType": {"select": {"name": "Internship"}},
        "Company": {"select": {"name": "Google"}},
        "Location": {"select": {"name": "USA"}},
        "Duration": {"select": {"name": "12 months"}}
    }
    new_page = client.create_page(new_page_properties)

    print(f"Page Already exist ? : {client.title_exists('Sample Random Page')}")

    # Get all page titles
    titles = client.get_page_titles()
    print(f"Titles in the database: {titles}")

    sms_client = SMSAPI(FREE_MOBILE_USER_ID, FREE_MOBILE_API_KEY)
    # sms_client.send_sms("Hello from VIE-Tracker!")

    # url = "https://mon-vie-via.businessfrance.fr/offres/recherche?query=&specializationsIds=212&specializationsIds=24&missionsTypesIds=1&gerographicZones=4"
    # scraper = JobScraper(url)
    # try:
    #     data = scraper.scrape()
    #     print(f"Total offers found: {data['total_offers']}")
    #     print(f"Scraped {len(data['offers'])} offers.")
        
    #     for offer in data['offers']:
    #         print(f"Title: {offer['Title']}\n"
    #               f"Company: {offer['Company']}\n"
    #               f"Location: {offer['Location']}\n"
    #               f"Contract Type: {offer['Contract Type']}\n"
    #               f"Duration: {offer['Duration']}\n"
    #               f"Views: {offer['Views']}\n"
    #               f"Candidates: {offer['Candidates']}\n"
    #               "-----------------------------")
    # finally:
    #     scraper.close_driver()