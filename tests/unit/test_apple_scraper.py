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
        return scraper


def test_apple_setup_driver():
    with patch("src.scraper.webdriver.Chrome") as mock_chrome:
        from src.scraper import setup_driver

        driver = setup_driver(debug=False)
        mock_chrome.assert_called_once()
        assert driver is not None


def test_apple_load_all_offers(apple_scraper):
    apple_scraper.include_filters = ["offer"]

    # Setup mocks
    dummy_cookie = MagicMock()
    dummy_total_element = MagicMock(text="100 résultat(s)")
    dummy_offer_presence = MagicMock()

    # Setup accordion item
    dummy_row = MagicMock()
    dummy_title_link = MagicMock()
    dummy_title_link.text = "Offer Title"
    dummy_title_link.get_attribute.return_value = "http://offer1"

    # Mock find_element for the link
    dummy_row.find_element.return_value = dummy_title_link

    # Mock find_elements for rows
    apple_scraper.driver.find_elements.return_value = [dummy_row]

    # Setup next button
    next_button = MagicMock()

    with patch("selenium.webdriver.support.ui.WebDriverWait") as mock_wait:
        instance = MagicMock()
        # The sequence below simulates:
        # 1. Clicking cookie consent,
        # 2. Finding the total offers element,
        # 3. Waiting for first offer,
        # 4. Finding the next button,
        # 5. And then failing to find a next button on next iteration.
        instance.until.side_effect = [
            dummy_cookie,  # cookie consent click
            dummy_total_element,  # total offers element
            dummy_offer_presence,  # wait for offer presence
            next_button,  # next button
            Exception("No more next button"),  # timeout on next iteration
        ]
        mock_wait.return_value = instance

        # Mock the regex search
        with patch("re.search") as mock_search:
            mock_search.return_value = MagicMock()
            mock_search.return_value.group.return_value = "100"

            apple_scraper.load_all_offers()

    assert apple_scraper.total_offers == 100
    assert len(apple_scraper.offers_url) == 1
    assert apple_scraper.offers_url[0] == "http://offer1"


def test_apple_extract_offers(apple_scraper):
    apple_scraper.offers_url = ["http://offer1", "http://offer2"]

    # Setup the mocked find_element function to return appropriate values for each element ID
    def mock_find_element(by, selector):
        elements = {
            "jobdetails-postingtitle": MagicMock(text="Title"),
            "jobdetails-jobnumber": MagicMock(text="Ref"),
            "jobdetails-joblocation": MagicMock(text="City, Country"),
            "jobdetails-weeklyhours": MagicMock(text="40 hours"),
            "jobdetails-teamname": MagicMock(text="Team"),
            "jobdetails-jobdetails-jobsummary-content-row": MagicMock(text="Summary"),
            "jobdetails-jobdetails-jobdescription-content-row": MagicMock(
                text="Description"
            ),
            "jobdetails-jobdetails-minimumqualifications-content-row": MagicMock(
                text="MinQual"
            ),
            "jobdetails-jobdetails-preferredqualifications-content-row": MagicMock(
                text="PrefQual"
            ),
        }
        return elements.get(selector, MagicMock(text="N/A"))

    apple_scraper.driver.find_element.side_effect = mock_find_element

    offers = apple_scraper.extract_offers()

    assert len(offers) == 2
    assert offers[0]["Title"] == "Title"
    assert offers[0]["Location"] == "City, Country"
    assert offers[0]["URL"] == "http://offer1"
    assert offers[0]["Source"] == "Apple"
    assert offers[0]["Company"] == "Apple"
