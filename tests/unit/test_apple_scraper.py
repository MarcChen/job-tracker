from unittest.mock import MagicMock, patch

import pytest

from src.job_scrapers.apple import AppleJobScraper


@pytest.fixture
def apple_scraper():
    with patch("src.scraper.setup_driver", return_value=MagicMock()):
        scraper = AppleJobScraper(url="http://apple.example.com")
        scraper.driver = MagicMock()
        # Patch the notion_client so that offer_exists accepts a third 'company' parameter.
        scraper.notion_client = MagicMock(
            offer_exists=lambda title, source, company: False
        )
        # Monkey-patch missing methods from the source code.
        scraper.should_skip_offer = lambda job_title: False
        scraper._init_offer_dict = lambda: {}
        # Also add extract_total_offers method to the instance.
        scraper.extract_total_offers = lambda: scraper.total_offers
        return scraper


def test_apple_setup_driver():
    with patch("src.scraper.webdriver.Chrome") as mock_chrome:
        from src.scraper import setup_driver

        driver = setup_driver(debug=False)
        mock_chrome.assert_called_once()
        assert driver is not None


def test_apple_load_all_offers(apple_scraper):
    apple_scraper.include_filters = ["offer"]
    dummy_cookie = MagicMock()
    dummy_total_element = MagicMock(text="1 offers")
    dummy_offer_presence = MagicMock()
    dummy_row = MagicMock()
    dummy_title_link = MagicMock()
    dummy_title_link.text = "Offer Title"
    dummy_title_link.get_attribute.return_value = "http://offer1"
    dummy_row.find_element.return_value = dummy_title_link
    apple_scraper.driver.find_elements.return_value = [dummy_row]
    with patch("selenium.webdriver.support.ui.WebDriverWait") as mock_wait:
        instance = MagicMock()
        # The sequence below simulates:
        # 1. Clicking cookie consent,
        # 2. Waiting for first offer,
        # 3. Finding the total offers element,
        # 4. Waiting again inside the loop,
        # 5. And then failing to find a next button.
        instance.until.side_effect = [
            dummy_cookie,  # cookie consent click
            dummy_offer_presence,  # wait for offer title presence
            dummy_total_element,  # total offers element (text "1 offers")
            dummy_offer_presence,  # wait inside loop for offer title
            Exception("No next button"),
        ]
        mock_wait.return_value = instance
        apple_scraper.load_all_offers()
    assert apple_scraper.total_offers == 1
    assert len(apple_scraper.offers_url) == 1
    assert apple_scraper.offers_url[0] == "http://offer1"


def test_apple_extract_offers(apple_scraper):
    apple_scraper.offers_url = ["http://offer1", "http://offer2"]
    dummy_elements = [
        # Offer 1 elements
        MagicMock(text="Title1"),
        MagicMock(text="Ref1"),
        MagicMock(text="City1, Country"),
        MagicMock(text="40 hours"),
        MagicMock(text="Team1"),
        MagicMock(text="Description1"),
        MagicMock(text="MinQual1"),
        MagicMock(text="PrefQual1"),
        # Offer 2 elements
        MagicMock(text="Title2"),
        MagicMock(text="Ref2"),
        MagicMock(text="City2, Country"),
        MagicMock(text="35 hours"),
        MagicMock(text="Team2"),
        MagicMock(text="Description2"),
        MagicMock(text="MinQual2"),
        MagicMock(text="PrefQual2"),
    ]
    apple_scraper.driver.find_element.side_effect = dummy_elements
    offers = apple_scraper.extract_offers()
    assert len(offers) == 2
    assert offers[0]["Title"] == "Title1"
    assert offers[0]["Location"] == "City1"
    assert offers[0]["URL"] == "http://offer1"
    assert offers[0]["Source"] == "Apple"


def test_apple_extract_total_offers(apple_scraper):
    apple_scraper.total_offers = 5
    total = apple_scraper.extract_total_offers()
    assert total == 5
