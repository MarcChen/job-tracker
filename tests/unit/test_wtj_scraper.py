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

    def test_extract_total_offers_initial(self):
        # Before loading, total_offers should be 0
        self.assertEqual(self.scraper.extract_total_offers(), 0)
        # Manually set total_offers and test extraction
        self.scraper.total_offers = 5
        self.assertEqual(self.scraper.extract_total_offers(), 5)

    def test_extract_offers_with_dummy_elements(self):
        # Prepare a dummy offers_url list
        self.scraper.offers_url = [
            "http://dummy-offer.com/job1",
            "http://dummy-offer.com/job2",
        ]
        # Call extract_offers which iterates over offers_url and calls driver.get and find_element.
        offers = self.scraper.extract_offers()
        # Expect as many offers as in offers_url
        self.assertEqual(len(offers), 2)
        # Check that some expected keys are present in each offer dictionary
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
            # URL should be equal to the dummy offer url.
            self.assertIn(offer["URL"], self.scraper.offers_url)


if __name__ == "__main__":
    unittest.main()
