from rich.progress import Progress, SpinnerColumn, TextColumn
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from services.databases.src.notion_integration import NotionClient
from services.job_scrapers.airfrance import AirFranceJobScraper
from services.job_scrapers.apple import AppleJobScraper
from services.job_scrapers.vie import VIEJobScraper
from services.job_scrapers.welcome_to_the_jungle import WelcomeToTheJungleJobScraper


def scrape_all_offers(
    driver, include_filters, exclude_filters, notion_client: NotionClient, debug=False
):
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
    url_air_france = (
        "https://recrutement.airfrance.com/offre-de-emploi/liste-offres.aspx"
    )
    url_apple = "https://jobs.apple.com/fr-fr/search?sort=relevance&location=france-FRAC+singapore-SGP+hong-kong-HKGC+taiwan-TWN"
    url_wtj = "https://www.welcometothejungle.com/fr/jobs?&refinementList%5Bcontract_type%5D%5B%5D=full_time&refinementList%5Bcontract_type%5D%5B%5D=temporary&refinementList%5Bcontract_type%5D%5B%5D=freelance"

    scraper_vie = VIEJobScraper(
        url_vie,
        driver=driver,
        include_filters=include_filters,
        exclude_filters=exclude_filters,
        debug=debug,
        notion_client=notion_client,
    )
    scraper_airfrance = AirFranceJobScraper(
        url=url_air_france,
        keyword="",
        contract_type="CDI",
        driver=driver,
        include_filters=include_filters,
        exclude_filters=exclude_filters,
        debug=debug,
        notion_client=notion_client,
    )
    scraper_apple = AppleJobScraper(
        url=url_apple,
        driver=driver,
        include_filters=include_filters,
        exclude_filters=exclude_filters,
        debug=debug,
        notion_client=notion_client,
    )

    scraper_wtj_data_engineer = WelcomeToTheJungleJobScraper(
        url=url_wtj,
        driver=driver,
        include_filters=include_filters,
        exclude_filters=exclude_filters,
        keyword="data engineer",
        location="Île-de-France",
        debug=debug,
        notion_client=notion_client,
    )

    scraper_wtj_data_ai = WelcomeToTheJungleJobScraper(
        url=url_wtj,
        driver=driver,
        include_filters=include_filters,
        exclude_filters=exclude_filters,
        keyword="artificial intelligence",
        location="Île-de-France",
        debug=debug,
        notion_client=notion_client,
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task_air = progress.add_task("[cyan]Scraping Air France offers...", total=None)
        data_Air_France = scraper_airfrance.scrape()
        progress.remove_task(task_air)

        task_vie = progress.add_task("[magenta]Scraping VIE offers...", total=None)
        data_VIE = scraper_vie.scrape()
        progress.remove_task(task_vie)

        task_apple = progress.add_task("[green]Scraping Apple offers...", total=None)
        data_apple = scraper_apple.scrape()
        progress.remove_task(task_apple)

        task_wtj = progress.add_task(
            "[yellow]Scraping Welcome to the Jungle Data Engineer offers...", total=None
        )
        data_wtj_data_engineer = scraper_wtj_data_engineer.scrape()
        progress.remove_task(task_wtj)

        task_wtj_ai = progress.add_task(
            "[yellow]Scraping Welcome to the Jungle AI offers...", total=None
        )
        data_wtj_ai = scraper_wtj_data_ai.scrape()
        progress.remove_task(task_wtj_ai)
        offers = (
            data_VIE
            + data_Air_France
            + data_apple
            + data_wtj_data_engineer
            + data_wtj_ai
        )
        print(f"Combined scrapped offers : {offers}") if debug else None
        return offers


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
