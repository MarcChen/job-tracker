from src.scraper import scrape_all_offers, setup_driver
from src.notion_integration import NotionClient
from src.offer_processor import OfferProcessor
import os


if __name__ == "__main__":
    INCLUDE_FILTERS = [
        "data engineer",
        "data scientist",
        "machine learning",
        "artificial intelligence",
        "big data",
        "science",
        "GCP",
        "Data platform",
        "Cloud Database",
        "deep learning",
        "software",
        "developer",
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
    DEBUG = False

    DATABASE_ID = os.getenv("DATABASE_ID")
    NOTION_API = os.getenv("NOTION_API")
    assert DATABASE_ID, "DATABASE_ID environment variable is not set."
    assert NOTION_API, "NOTION_API environment variable is not set."
    notion_client = NotionClient(NOTION_API, DATABASE_ID)
    try:
        driver = setup_driver(debug=DEBUG)
        data = scrape_all_offers(driver, INCLUDE_FILTERS, EXCLUDE_FILTERS, debug=DEBUG, notion_client=notion_client)
        print(f"Finished loading all available offers. Processing {len(data)} offers...")
    finally:
        driver.quit()
    processor = OfferProcessor(data, notion_client=notion_client)
    processor.process_offers()
