from unittest.mock import MagicMock, patch

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from src.job_scrapers.job_scraper_base import JobScraperBase
from src.job_scrapers.vie import VIEJobScraper


@pytest.fixture
def vie_scraper():
    with patch("src.scraper.setup_driver", return_value=MagicMock()):
        scraper = VIEJobScraper(url="http://example.com")
        scraper.driver = MagicMock()
        return scraper


def test_vie_load_all_offers(vie_scraper):
    vie_scraper.driver.find_elements.return_value = [MagicMock()] * 5
    with patch("selenium.webdriver.support.ui.WebDriverWait") as mock_wait:
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.side_effect = [
            MagicMock(),  # clickable button
            TimeoutException(),  # timeout to load more offers
        ]
        vie_scraper.load_all_offers()
    vie_scraper.driver.get.assert_called_once_with("http://example.com")


def test_vie_extract_offers(vie_scraper):
    mock_offer = MagicMock()
    mock_offer.find_element.side_effect = lambda by, value: MagicMock(
        text={
            (By.TAG_NAME, "h2"): "Test Title",
            (By.CLASS_NAME, "organization"): "Test Company",
            (By.CLASS_NAME, "location"): "Test Location",
        }[(by, value)]
    )
    mock_offer.find_elements.return_value = [
        MagicMock(text="Full-time"),
        MagicMock(text="3 months"),
        MagicMock(text="100"),
        MagicMock(text="5"),
    ]
    vie_scraper.driver.find_elements.return_value = [mock_offer] * 3
    offers = vie_scraper.extract_offers()
    assert len(offers) == 3
    assert offers[0]["Source"] == "Business France"


def test_vie_extract_total_offers(vie_scraper):
    vie_scraper.driver.find_element.return_value = MagicMock(text="100 offers")
    total = vie_scraper.extract_total_offers()
    assert total == 100


def test_vie_scrape_and_close_driver(vie_scraper):
    def base_close(self):
        if self.driver:
            self.driver.quit()

    JobScraperBase.close_driver = base_close

    vie_scraper.load_all_offers = MagicMock()
    vie_scraper.extract_offers = MagicMock(
        return_value=[
            {
                "Title": "Test Offer",
                "Company": "Test Company",
                "Location": "Test Location",
                "Source": "Business France",
            }
        ]
    )
    vie_scraper.extract_total_offers = MagicMock(return_value=1)
    result = vie_scraper.scrape()
    assert result["total_offers"] == 1
    assert len(result["offers"]) == 1

    vie_scraper.close_driver()
    vie_scraper.driver.quit.assert_called_once()
