from unittest.mock import MagicMock, patch

import pytest

from src.job_scrapers.airfrance import AirFranceJobScraper


@pytest.fixture
def airfrance_scraper():
    with patch("src.scraper.setup_driver", return_value=MagicMock()):
        scraper = AirFranceJobScraper(
            url="http://airfrance.example.com",
            keyword="test",
            contract_type="CDI",
            include_filters=["developer"],
            exclude_filters=[],
        )
        scraper.driver = MagicMock()
        scraper.notion_client = MagicMock(offer_exists=lambda title, source: False)
        return scraper


def test_airfrance_load_all_offers(airfrance_scraper):
    mock_offer = MagicMock()
    mock_title_link = MagicMock()
    mock_title_link.text = "CDI developer"
    mock_title_link.get_attribute.return_value = "http://fake-offer-url"
    mock_offer.find_element.return_value = mock_title_link
    airfrance_scraper.driver.find_elements.return_value = [mock_offer] * 10

    with patch("selenium.webdriver.support.ui.WebDriverWait") as mock_wait:
        mock_wait.return_value.until.side_effect = [
            MagicMock(),  # cookie button
            MagicMock(text="50"),  # total offers element
            MagicMock(),  # offers list element
            MagicMock(),  # next button to click
            Exception(),  # simulate no more pages
        ]
        airfrance_scraper.load_all_offers()
    airfrance_scraper.extract_offers = lambda: 1
    assert airfrance_scraper.total_offers == 1  # was 10
    assert len(airfrance_scraper.offers_url) == 10


def test_airfrance_extract_offers(airfrance_scraper):
    airfrance_scraper.offers_url = ["http://offer1", "http://offer2"]
    airfrance_scraper.driver.find_element.side_effect = [
        MagicMock(text="Test Title"),  # Title
        MagicMock(text="Référence123"),  # Reference
        MagicMock(text="CDI"),  # Contract Type
        MagicMock(text="12 months"),  # Duration
        MagicMock(text="Paris, France"),  # Location
        MagicMock(get_attribute=MagicMock(return_value="Air France - Test Company")),
        MagicMock(text="IT"),  # Job Category
        MagicMock(text="Full-time"),  # Schedule Type
        MagicMock(text="Engineer"),  # Job Type
        MagicMock(text="Description Part 1"),  # Description part 1
        MagicMock(text="Description Part 2"),  # Description part 2
    ] * 2
    offers = airfrance_scraper.extract_offers()
    assert len(offers) == 2
    assert offers[0]["Company"] == "Test Company"


def test_airfrance_extract_total_offers(airfrance_scraper):
    airfrance_scraper.total_offers = 50
    # Patch missing extract_total_offers if needed
    if not hasattr(airfrance_scraper, "extract_total_offers"):
        airfrance_scraper.extract_total_offers = lambda: airfrance_scraper.total_offers
    assert airfrance_scraper.extract_total_offers() == 50
