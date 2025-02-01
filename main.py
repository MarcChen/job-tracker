import os

from rich.progress import Progress, SpinnerColumn, TextColumn

from src.notion_client import NotionClient
from src.selenium_script import (AirFranceJobScraper, AppleJobScraper,
                                 VIEJobScraper, setup_driver)
from src.sms_alert import SMSAPI

if __name__ == "__main__":
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

    notion_client = NotionClient(NOTION_API, DATABASE_ID)
    sms_client = SMSAPI(FREE_MOBILE_USER_ID, FREE_MOBILE_API_KEY)

    INCLUDE_FILTERS = [
        "data",
        "machine learning",
        "artificial intelligence",
        "big data",
        "science",
        "deep learning",
        "deep",
        "learning",
        "neural networks",
        "computer vision",
        "vision",
        "data mining",
        "predictive modeling",
        "language processing",
    ]
    EXCLUDE_FILTERS = [
        "internship",
        "stage",
        "intern",
        "internship",
        "apprenticeship",
        "apprentice",
        "alternance",
    ]

    driver = setup_driver(debug=True)

    url_vie = (
        "https://mon-vie-via.businessfrance.fr/offres/recherche?query=Data"
    )
    scraper_vie = VIEJobScraper(
        url_vie,
        driver=driver,
        include_filters=INCLUDE_FILTERS,
        exclude_filters=EXCLUDE_FILTERS,
    )

    url_air_france = (
        "https://recrutement.airfrance.com/offre-de-emploi/liste-offres.aspx"
    )
    scraper_airfrance = AirFranceJobScraper(
        url=url_air_france,
        keyword="",
        contract_type="CDI",
        driver=driver,
        include_filters=INCLUDE_FILTERS,
        exclude_filters=EXCLUDE_FILTERS,
    )

    url_apple = "https://jobs.apple.com/fr-fr/search?sort=relevance&location=france-FRAC+singapore-SGP+hong-kong-HKGC+taiwan-TWN"
    scraper_apple = AppleJobScraper(
        url=url_apple,
        driver=driver,
        include_filters=INCLUDE_FILTERS,
        exclude_filters=EXCLUDE_FILTERS,
    )

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,  # Remove the spinner after task completion
        ) as progress:
            # Air France scraping
            task_air = progress.add_task(
                "[cyan]Scraping Air France offers...", total=None
            )
            data_Air_France = (
                scraper_airfrance.scrape()
            )  # Your existing scraping call
            progress.remove_task(task_air)

            # VIE scraping
            task_vie = progress.add_task(
                "[magenta]Scraping VIE offers...", total=None
            )
            data_VIE = scraper_vie.scrape()
            progress.remove_task(task_vie)

            # Apple scraping
            task_apple = progress.add_task(
                "[green]Scraping Apple offers...", total=None
            )
            scraper_apple.load_all_offers()
            data_apple = scraper_apple.scrape()
            progress.remove_task(task_apple)
    finally:
        driver.quit()

    data = {
            "total_offers": data_VIE['total_offers'] + data_Air_France['total_offers'] + data_apple['total_offers'],
            "offers": data_VIE['offers'] + data_Air_France['offers'] + data_apple['offers']
        }
    print(f"Total offers found: {data['total_offers']}")

    try:
        with Progress() as progress:
            task = progress.add_task("Processing job offers...", total=len(data['offers']))
            for offer in data['offers']:
                title = offer['Title']

                if not any(keyword.lower() in title.strip().lower() for keyword in ["data", "ai", "ml", "machine learning", "artificial intelligence", "big data"]):
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
                                content = offer[field]
                                if len(content) > 2000:
                                    content = content[:2000]
                                    print(f"[yellow]Warning: {field} content clipped to 2000 characters.[/yellow]")
                                job_properties[field] = {
                                    "rich_text": [
                                        {"type": "text", "text": {"content": content}}
                                    ]
                                }
                            else:
                                job_properties[field] = {"select": {"name": offer[field]}}
                    notion_client.create_page(job_properties)
                    progress.console.log(f"[green]Job '{title}' added to Notion and SMS sent![/green]")
                    progress.advance(task)

    except Exception as e:
        print(f"Error processing scraped job offers: {e}")
