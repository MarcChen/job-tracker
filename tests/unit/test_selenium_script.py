import pytest
from unittest.mock import MagicMock, patch
from selenium.webdriver.common.by import By
from selenium_script import JobScraper  # Assuming the class is in a file named selenium_script.py

@pytest.fixture
def scraper():
    with patch("selenium_script.JobScraper._setup_driver", return_value=MagicMock()):
        scraper = JobScraper(url="http://example.com")
        return scraper

def test_setup_driver():
    with patch("selenium_script.webdriver.Chrome") as mock_driver:
        scraper = JobScraper(url="http://example.com")
        driver = scraper._setup_driver()
        assert mock_driver.called, "WebDriver should be initialized"
        assert driver is not None, "Driver should not be None"

def test_load_all_offers(scraper):
    scraper.driver.find_elements.return_value = [MagicMock()] * 5

    with patch("selenium.webdriver.support.ui.WebDriverWait.until") as mock_wait:
        mock_wait.side_effect = [
            MagicMock(),  # Simulate clickable button
            True  # Simulate increase in offers
        ]
        scraper.load_all_offers()

    scraper.driver.get.assert_called_once_with("http://example.com")
    assert scraper.driver.execute_script.call_count > 0, "Scroll and click should be executed"

def test_extract_offers(scraper):
    mock_offer = MagicMock()
    mock_offer.find_element.side_effect = lambda by, value: MagicMock(
        text={
            (By.TAG_NAME, "h2"): "Test Title",          # Simulating the title
            (By.CLASS_NAME, "organization"): "Test Company",  # Simulating the company
            (By.CLASS_NAME, "location"): "Test Location"      # Simulating the location
        }.get((by, value), "Default Value")
    )
    mock_offer.find_elements.return_value = [
        MagicMock(text="Full-time"),          # Contract type
        MagicMock(text="3 months"),           # Duration
        MagicMock(text="100"),                # Views (string to match the real implementation)
        MagicMock(text="5")                   # Candidates
    ]

    scraper.driver.find_elements.return_value = [mock_offer] * 3
    offers = scraper.extract_offers()

    assert len(offers) == 3, "Should extract three offers"
    assert offers[0]["Title"] == "Test Title", "Title should be extracted correctly"
    assert offers[0]["Company"] == "Test Company", "Company should be extracted correctly"
    assert offers[0]["Location"] == "Test Location", "Location should be extracted correctly"
    assert offers[0]["Contract Type"] == "Full-time", "Contract Type should be extracted correctly"
    assert offers[0]["Duration"] == "3 months", "Duration should be extracted correctly"
    assert int(offers[0]["Views"]) == 100, "Views should be extracted correctly"  # Convert to int for comparison
    assert int(offers[0]["Candidates"]) == 5, "Candidates should be extracted correctly"  # Convert to int for comparison

def test_extract_total_offers(scraper):
    scraper.driver.find_element.return_value = MagicMock(text="100 offers")
    total_offers = scraper.extract_total_offers()

    assert total_offers == 100, "Total offers should be extracted as an integer"

def test_scrape(scraper):
    scraper.load_all_offers = MagicMock()
    scraper.extract_offers = MagicMock(return_value=[{"Title": "Test Offer"}])
    scraper.extract_total_offers = MagicMock(return_value=10)

    result = scraper.scrape()

    assert result["total_offers"] == 10, "Total offers count should be 10"
    assert len(result["offers"]) == 1, "Offers list should contain one offer"

def test_close_driver(scraper):
    scraper.close_driver()
    scraper.driver.quit.assert_called_once(), "Driver.quit should be called once"
