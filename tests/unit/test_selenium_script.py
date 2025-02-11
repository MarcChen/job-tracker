from unittest.mock import patch

from src.scraper import setup_driver


def test_setup_driver():
    with patch("src.scraper.webdriver.Chrome") as mock_chrome:
        driver = setup_driver(debug=False)
        mock_chrome.assert_called_once()
        assert driver is not None
