from src.offer_processor import OfferProcessor
from src.scraper import scrape_all_offers, setup_driver

if __name__ == "__main__":
    INCLUDE_FILTERS = [
        "data",
        "machine learning",
        "artificial intelligence",
        "big data",
        "science",
        "deep learning",
        "deep",
        "software",
        "developer",
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
    DEBUG = False

    try:
        driver = setup_driver(debug=DEBUG)
        data = scrape_all_offers(driver, INCLUDE_FILTERS, EXCLUDE_FILTERS, debug=DEBUG)
    finally:
        driver.quit()
    print(f"Total offers found: {data['total_offers']}")

    processor = OfferProcessor(data)
    processor.process_offers()
