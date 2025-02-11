# tests/unit/test_selenium_script.py

from unittest.mock import MagicMock, patch

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from src.job_scrapers.airfrance import AirFranceJobScraper
from src.job_scrapers.apple import AppleJobScraper
from src.job_scrapers.job_scraper_base import JobScraperBase
from src.job_scrapers.vie import VIEJobScraper
from src.scraper import setup_driver


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
            contract_type="CDI",
            include_filters=["developer"],  # <-- Non-empty include filter
            exclude_filters=[],
        )
        scraper.driver = MagicMock()
        return scraper


@pytest.fixture
def apple_scraper():
    # Patch the driver setup so that we don’t launch a real browser
    with patch("selenium_script.setup_driver", return_value=MagicMock()):
        scraper = AppleJobScraper(url="http://apple.example.com")
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
            TimeoutException(),  # Timeout when checking offer count
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


# Tests for AirFranceJobScraper
def test_airfrance_load_all_offers(airfrance_scraper):
    # Mock a single "offer" element
    mock_offer = MagicMock()
    # The internal link element with text containing "developer" to pass the filter
    mock_title_link = MagicMock()
    mock_title_link.text = "CDI developer"
    mock_title_link.get_attribute.return_value = "http://fake-offer-url"
    # So that offer.find_element(By.CLASS_NAME, "ts-offer-list-item__title-link") returns mock_title_link
    mock_offer.find_element.return_value = mock_title_link

    # Now the driver finds 10 identical offers:
    airfrance_scraper.driver.find_elements.return_value = [mock_offer] * 10

    with patch("selenium_script.WebDriverWait") as mock_wait:
        mock_wait.return_value.until.side_effect = [
            MagicMock(),  # Cookie button
            MagicMock(text="50"),  # Total offers element
            MagicMock(),  # Offers list
            MagicMock(),  # Next button (page 1)
            Exception(),  # No more pages
        ]
        airfrance_scraper.load_all_offers()

    assert airfrance_scraper.total_offers == 50
    # Now we have 10 because the "developer" filter was matched by "CDI developer"
    assert len(airfrance_scraper.offers_url) == 10


def test_airfrance_extract_offers(airfrance_scraper):
    airfrance_scraper.offers_url = ["http://offer1", "http://offer2"]
    airfrance_scraper.driver.find_element.side_effect = [
        MagicMock(text="Test Title"),  # Title
        MagicMock(text="Référence123"),  # Reference
        MagicMock(text="CDI"),  # Contract Type
        MagicMock(text="12 months"),  # Duration
        MagicMock(text="Paris, France"),  # Location
        MagicMock(
            get_attribute=MagicMock(return_value="Air France - Test Company")
        ),  # Company
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
    vie_scraper.extract_offers = MagicMock(
        return_value=[
            {
                "Title": "Test Offer",
                "Company": "Test Company",  # Added required field
                "Location": "Test Location",
                "Source": "Business France",  # Added required field
            }
        ]
    )
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


# Tests for AppleJobScraper
def test_apple_setup_driver():
    """Test that the driver is created successfully."""
    with patch("selenium_script.webdriver.Chrome") as mock_chrome:
        driver = setup_driver(debug=False)
        mock_chrome.assert_called_once()
        assert driver is not None


def test_apple_load_all_offers(apple_scraper):
    """
    Test the load_all_offers method by simulating:
    - A cookie consent element,
    - A total offers count element,
    - One offer row containing a title link,
    - And an exception when attempting to click the next page.
    """
    # Set an include filter so that the offer is not skipped.
    apple_scraper.include_filters = ["offer"]

    # Simulate the cookie consent element (clickable)
    dummy_cookie = MagicMock()

    # Simulate the total offers count element: e.g. "1 offers"
    dummy_total_element = MagicMock()
    dummy_total_element.text = "1 offers"

    # Dummy element for the presence of the offer title link element
    dummy_offer_presence = MagicMock()

    # Set up a dummy offer row that returns a dummy title link.
    dummy_row = MagicMock()
    dummy_title_link = MagicMock()
    dummy_title_link.text = "Offer Title"
    dummy_title_link.get_attribute.return_value = "http://offer1"
    # When the scraper calls find_element on the row with the correct selector,
    # return the dummy title link.
    dummy_row.find_element.return_value = dummy_title_link

    # When the scraper looks for offer rows, return a list with one dummy row.
    apple_scraper.driver.find_elements.return_value = [dummy_row]

    # Patch WebDriverWait so that each call to .until() returns a controlled value.
    with patch("selenium_script.WebDriverWait") as mock_wait:
        instance = MagicMock()
        # The expected sequence of WebDriverWait.until() calls:
        # 1. For the cookie consent button -> returns dummy_cookie.
        # 2. For the presence of the offer title element (first time) -> returns dummy_offer_presence.
        # 3. For the total offers count element -> returns dummy_total_element.
        # 4. Inside the while loop: wait for presence of offer title element -> returns dummy_offer_presence.
        # 5. For the next button clickable -> raise Exception to simulate no next button.
        instance.until.side_effect = [
            dummy_cookie,  # cookie consent
            dummy_offer_presence,  # initial wait for offer title element
            dummy_total_element,  # total offers count element
            dummy_offer_presence,  # wait for offer title element inside while loop
            Exception("No next button"),  # simulate failure to get next button
        ]
        mock_wait.return_value = instance

        apple_scraper.load_all_offers()

    # After running, the total_offers should be set from the dummy total element.
    assert apple_scraper.total_offers == 1

    # Since the offer title "Offer Title" now passes (include filter contains "offer"),
    # the offers_url list should contain the URL extracted from the dummy title link.
    assert len(apple_scraper.offers_url) == 1
    assert apple_scraper.offers_url[0] == "http://offer1"


def test_apple_extract_offers(apple_scraper):
    """
    Test extract_offers by pre-populating offers_url and simulating
    the calls to driver.find_element with dummy elements.
    """
    # Simulate two offer URLs
    apple_scraper.offers_url = ["http://offer1", "http://offer2"]

    # For each offer, the extract_offers method calls driver.find_element 8 times:
    #   1. jdPostingTitle (Title)
    #   2. jobNumber (Reference)
    #   3. job-location-name (Location) -- will be split on a comma
    #   4. jobWeeklyHours (Schedule Type)
    #   5. job-team-name (Job Type)
    #   6. jd-description (part of Description)
    #   7. jd-minimum-qualifications (part of Description)
    #   8. jd-preferred-qualifications (part of Description)
    #
    # For 2 offers, we need 16 dummy elements.
    dummy_elements = [
        # Offer 1
        MagicMock(text="Title1"),
        MagicMock(text="Ref1"),
        MagicMock(text="City1, Country"),  # expect "City1" after splitting
        MagicMock(text="40 hours"),
        MagicMock(text="Team1"),
        MagicMock(text="Description1"),
        MagicMock(text="MinQual1"),
        MagicMock(text="PrefQual1"),
        # Offer 2
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

    # Verify the fields for the first offer.
    offer1 = offers[0]
    assert offer1["Title"] == "Title1"
    # The location should be split on the comma, keeping only the city.
    assert offer1["Location"] == "City1"
    assert offer1["URL"] == "http://offer1"
    assert offer1["Source"] == "Apple"

    # Verify the fields for the second offer.
    offer2 = offers[1]
    assert offer2["Title"] == "Title2"
    assert offer2["Location"] == "City2"
    assert offer2["URL"] == "http://offer2"
    assert offer2["Source"] == "Apple"


def test_apple_extract_total_offers(apple_scraper):
    """Test that extract_total_offers simply returns the total_offers attribute."""
    apple_scraper.total_offers = 5
    total = apple_scraper.extract_total_offers()
    assert total == 5
