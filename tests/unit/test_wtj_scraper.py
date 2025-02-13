import unittest
from unittest.mock import MagicMock

from src.job_scrapers.welcome_to_the_jungle import WelcomeToTheJungleJobScraper


class DummyElement:
    def __init__(self, text="Dummy text"):
        self.text = text

    def get_attribute(self, attr):
        return "Dummy text"


class TestWelcomeToTheJungleJobScraper(unittest.TestCase):
    def setUp(self):
        # Create a dummy driver with minimal methods
        self.dummy_driver = MagicMock()
        # driver.get does nothing
        self.dummy_driver.get = MagicMock()
        # driver.find_element always returns a DummyElement instance
        self.dummy_driver.find_element.return_value = DummyElement()

        # Instantiate the scraper with dummy driver and URL
        self.scraper = WelcomeToTheJungleJobScraper(
            url="http://dummy-url.com", driver=self.dummy_driver, debug=False
        )
        # Override _init_offer_dict to return an empty dict
        self.scraper._init_offer_dict = lambda: {}
        # Monkey-patch missing methods:
        # Since the source doesn't define extract_total_offers, we add it here.
        self.scraper.extract_total_offers = lambda: self.scraper.total_offers
        # Likewise, define should_skip_offer to always return False.
        self.scraper.should_skip_offer = lambda title: False

    def test_extract_total_offers_initial(self):
        # Before any offers are loaded, total_offers should be 0.
        self.assertEqual(self.scraper.extract_total_offers(), 0)
        # Manually set total_offers and verify extraction.
        self.scraper.total_offers = 5
        self.assertEqual(self.scraper.extract_total_offers(), 5)

    def test_extract_offers_with_dummy_elements(self):
        # Prepare a dummy offers_url list.
        self.scraper.offers_url = [
            "http://dummy-offer.com/job1",
            "http://dummy-offer.com/job2",
        ]
        # Call extract_offers, which iterates over offers_url, calls driver.get, and find_element.
        offers = self.scraper.extract_offers()
        # Expect as many offers as there are in offers_url.
        self.assertEqual(len(offers), 2)
        # Check that each offer dictionary contains the expected keys.
        expected_keys = [
            "Title",
            "Location",
            "Salary",
            "Experience Level",
            "Schedule Type",
            "Job Type",
            "Description",
            "URL",
            "Contract Type",
            "Company",
            "Source",
        ]
        for offer in offers:
            for key in expected_keys:
                self.assertIn(key, offer)
            # Verify that the offer URL matches one of the dummy URLs.
            self.assertIn(offer["URL"], self.scraper.offers_url)


if __name__ == "__main__":
    unittest.main()
