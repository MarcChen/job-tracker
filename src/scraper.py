from curses import raw
import random
import time
import warnings
from typing import Dict, List, Union

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from rich.progress import Progress, SpinnerColumn, TextColumn
from src.job_scrapers.vie import VIEJobScraper
from src.job_scrapers.airfrance import AirFranceJobScraper
from src.job_scrapers.apple import AppleJobScraper


def scrape_all_offers(driver, include_filters, exclude_filters, debug=False):
    """
    Scrapes job offers from three different job portals: VIE, Air France, and Apple.
    This function creates a scraper for each source website using the appropriate scraper class, initiates the scraping process while displaying a progress spinner, and then aggregates the results.
    Parameters:
        driver (webdriver): The Selenium WebDriver instance to interact with web pages.
        include_filters (list or dict): Criteria to filter in job offers; structure depends on implementation details of each scraper.
        exclude_filters (list or dict): Criteria to filter out job offers; structure depends on implementation details of each scraper.
        debug (bool, optional): If set to True, additional debugging information will be printed. Defaults to False.
    Returns:
        dict: A dictionary with two keys:
            - "total_offers": An integer representing the sum of the total offers found across all portals.
            - "offers": A list containing all the offers scraped from the VIE, Air France, and Apple job portals.
    """
    url_vie = "https://mon-vie-via.businessfrance.fr/offres/recherche?query=Data"
    url_air_france = "https://recrutement.airfrance.com/offre-de-emploi/liste-offres.aspx"
    url_apple = "https://jobs.apple.com/fr-fr/search?sort=relevance&location=france-FRAC+singapore-SGP+hong-kong-HKGC+taiwan-TWN"
    
    scraper_vie = VIEJobScraper(url_vie, driver=driver, include_filters=include_filters, exclude_filters=exclude_filters, debug=debug)
    scraper_airfrance = AirFranceJobScraper(
        url=url_air_france, keyword="", contract_type="CDI",
        driver=driver, include_filters=include_filters, exclude_filters=exclude_filters, debug=debug
    )
    scraper_apple = AppleJobScraper(url=url_apple, driver=driver, include_filters=include_filters, exclude_filters=exclude_filters, debug=debug)
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        task_air = progress.add_task("[cyan]Scraping Air France offers...", total=None)
        data_Air_France = scraper_airfrance.scrape()
        progress.remove_task(task_air)
        
        task_vie = progress.add_task("[magenta]Scraping VIE offers...", total=None)
        data_VIE = scraper_vie.scrape()
        progress.remove_task(task_vie)
        
        task_apple = progress.add_task("[green]Scraping Apple offers...", total=None)
        data_apple = scraper_apple.scrape()
        progress.remove_task(task_apple)
    
    # Merge scraped data and return
    total_offers = data_VIE['total_offers'] + data_Air_France['total_offers'] + data_apple['total_offers']
    offers = data_VIE['offers'] + data_Air_France['offers'] + data_apple['offers']
    print(f"All scrapped offers : {offers}") if debug else None
    return {"total_offers": total_offers, "offers": offers}


def setup_driver(debug: bool = False) -> webdriver.Chrome:
    """
    Set up the Selenium WebDriver with necessary options.

    Returns:
        webdriver.Chrome: Configured Selenium WebDriver instance.
    """
    if not debug:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--start-maximized")  # Open in full screen
        chrome_options.binary_location = "/usr/bin/chromium"
        service = Service("/usr/bin/chromedriver")

        return webdriver.Chrome(service=service, options=chrome_options)
    else:
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")  # Open in full screen

        # Use Remote WebDriver to connect to the Selenium container
        driver = webdriver.Remote(
            command_executor="http://localhost:4444/wd/hub", options=options
        )
        return driver