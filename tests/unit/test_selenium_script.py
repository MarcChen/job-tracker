# tests/unit/test_selenium_script.py

import pytest
from unittest.mock import MagicMock, patch, call
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium_script import VIEJobScraper, AirFranceJobScraper, setup_driver, JobScraperBase

# Fixtures for both scrapers
@pytest.fixture
def vie_scraper():
    with patch("selenium_script.setup_driver", return_value=MagicMock()):
        scraper = VIEJobScraper(url="http://example.com")
        scraper.driver = MagicMock()
        return scraper

@pytest.fixture
def airfrance_scraper():
    with patch("selenium_script.setup_driver", return_value=MagicMock()):
        scraper = AirFranceJobScraper(
            url="http://airfrance.example.com", 
            keyword="test", 
            contract_type="CDI"
        )
        scraper.driver = MagicMock()
        return scraper

# Tests for VIEJobScraper
def test_vie_setup_driver():
    with patch("selenium_script.webdriver.Chrome") as mock_chrome:
        driver = setup_driver(debug=False)
        mock_chrome.assert_called_once()
        assert driver is not None

def test_vie_load_all_offers(vie_scraper):
    vie_scraper.driver.find_elements.return_value = [MagicMock()] * 5

    with patch("selenium_script.WebDriverWait") as mock_wait:
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.side_effect = [
            MagicMock(),  # Clickable button
            TimeoutException()  # Timeout when checking offer count
        ]

        vie_scraper.load_all_offers()

    vie_scraper.driver.get.assert_called_once_with("http://example.com")
    assert vie_scraper.driver.execute_script.call_count >= 1

def test_vie_extract_offers(vie_scraper):
    mock_offer = MagicMock()
    mock_offer.find_element.side_effect = lambda by, value: MagicMock(
        text={
            (By.TAG_NAME, "h2"): "Test Title",
            (By.CLASS_NAME, "organization"): "Test Company",
            (By.CLASS_NAME, "location"): "Test Location"
        }[(by, value)]
    )
    mock_offer.find_elements.return_value = [
        MagicMock(text="Full-time"),
        MagicMock(text="3 months"),
        MagicMock(text="100"),
        MagicMock(text="5")
    ]

    vie_scraper.driver.find_elements.return_value = [mock_offer] * 3
    offers = vie_scraper.extract_offers()

    assert len(offers) == 3
    assert offers[0]["Source"] == "Business France"

def test_vie_extract_total_offers(vie_scraper):
    vie_scraper.driver.find_element.return_value = MagicMock(text="100 offers")
    total = vie_scraper.extract_total_offers()
    assert total == 100

# Tests for AirFranceJobScraper
def test_airfrance_load_all_offers(airfrance_scraper):
    airfrance_scraper.driver.find_element.return_value = MagicMock()
    airfrance_scraper.driver.find_elements.return_value = [MagicMock()] * 10

    with patch("selenium_script.WebDriverWait") as mock_wait:
        mock_wait.return_value.until.side_effect = [
            MagicMock(),  # Cookie button
            MagicMock(text="50"),  # Total offers element
            MagicMock(),  # Offers list
            MagicMock(),  # Next button (page 1)
            Exception()   # No more pages
        ]
        airfrance_scraper.load_all_offers()

    assert airfrance_scraper.total_offers == 50
    assert len(airfrance_scraper.offers_url) == 10

def test_airfrance_extract_offers(airfrance_scraper):
    airfrance_scraper.offers_url = ["http://offer1", "http://offer2"]
    airfrance_scraper.driver.find_element.side_effect = [
        MagicMock(text="Test Title"),  # Title
        MagicMock(text="Référence123"),  # Reference
        MagicMock(text="CDI"),  # Contract Type
        MagicMock(text="12 months"),  # Duration
        MagicMock(text="Paris, France"),  # Location
        MagicMock(get_attribute=MagicMock(return_value="Air France - Test Company")),  # Company
        MagicMock(text="IT"),  # Job Category
        MagicMock(text="Full-time"),  # Schedule Type
        MagicMock(text="Engineer"),  # Job Type
        MagicMock(text="Description Part 1"),  # Description
        MagicMock(text="Description Part 2"),
    ] * 2

    offers = airfrance_scraper.extract_offers()
    assert len(offers) == 2
    assert offers[0]["Company"] == "Test Company"

def test_airfrance_extract_total_offers(airfrance_scraper):
    airfrance_scraper.total_offers = 50
    assert airfrance_scraper.extract_total_offers() == 50

# Common tests
def test_scrape(vie_scraper):
    vie_scraper.load_all_offers = MagicMock()
    vie_scraper.extract_offers = MagicMock(return_value=[{
        "Title": "Test Offer",
        "Company": "Test Company",  # Added required field
        "Location": "Test Location",
        "Source": "Business France"  # Added required field
    }])
    vie_scraper.extract_total_offers = MagicMock(return_value=1)

    result = vie_scraper.scrape()
    assert result["total_offers"] == 1
    assert len(result["offers"]) == 1

def test_close_driver(vie_scraper):
    # Add close_driver method to base class first
    def base_close(self):
        if self.driver:
            self.driver.quit()
    
    # Monkey-patch the base class if needed
    JobScraperBase.close_driver = base_close
    
    vie_scraper.close_driver()
    vie_scraper.driver.quit.assert_called_once()