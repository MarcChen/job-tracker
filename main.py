import argparse
import logging
import os
from typing import Dict, List

from rich.logging import RichHandler

from services.processing.src.offer_processor import OfferProcessor
from services.scraping.src.config import get_default_filters, get_scrapers_config
from services.storage.src.notion_integration import NotionClient


def parse_scraper_selection(  # noqa: C901
    selection: str, scrapers_config: Dict[str, dict]
) -> List[str]:
    """Parse scraper selection from command line argument."""
    selection = selection.lower().strip()

    # Pre-defined groups for easier selection
    if selection == "all":
        return list(scrapers_config.keys())
    elif selection in ["vie", "business-france", "businessfrance"]:
        return ["1"]
    elif selection == "cdi":
        return ["2", "3", "4", "5", "6"]
    elif selection in ["tech", "technology"]:
        return ["3", "4", "5", "6"]
    elif selection in ["wttj", "welcome-to-the-jungle"]:
        return ["4", "5"]
    elif selection in ["airfrance", "air-france"]:
        return ["2"]
    elif selection == "apple":
        return ["3"]
    elif selection == "linkedin":
        return ["6"]
    elif selection in ["data", "data-engineer", "dataengineer"]:
        return ["4", "6"]
    elif selection in ["ai", "artificial-intelligence"]:
        return ["5", "6"]
    elif selection in ["french-companies", "france"]:
        return ["1", "2"]  # VIE and Air France
    else:
        # Parse comma-separated list or individual IDs
        selected = [s.strip() for s in selection.split(",")]
        valid_ids = []
        for s in selected:
            if s in scrapers_config:
                valid_ids.append(s)
            else:
                raise ValueError(
                    f"Invalid scraper ID: {s}. Available options: {', '.join(scrapers_config.keys())}"
                )
        return valid_ids


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="VIE Job Tracker - Automated job scraping",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Scraper Selection Options:
  all               - Run all scrapers (1,2,3,4,5,6)
  vie               - VIE-focused scrapers (1) [alias: business-france, businessfrance]
  cdi               - CDI-focused scrapers (2,3,4,5,6)
  tech              - Tech company scrapers (3,4,5,6) [alias: technology]
  wttj              - Welcome to the Jungle scrapers (4,5) [alias: welcome-to-the-jungle]
  french-companies  - French companies (1,2) [alias: france]
  airfrance         - Air France only (2) [alias: air-france]
  apple             - Apple only (3)
  linkedin          - LinkedIn only (6)
  data              - Data Engineer roles (4,6) [alias: data-engineer, dataengineer]
  ai                - AI roles (5,6) [alias: artificial-intelligence]
  1,3,5,6           - Specific scrapers by ID (comma-separated)

Available Scrapers:
  1 - Business France (VIE)
  2 - Air France
  3 - Apple
  4 - Welcome to the Jungle (Data Engineer)
  5 - Welcome to the Jungle (AI)
  6 - LinkedIn

Examples:
  python main.py --scrapers all
  python main.py --scrapers vie --debug
  python main.py --scrapers apple
  python main.py --scrapers 1,3,5,6
  python main.py --list-scrapers
  python main.py --scrapers tech --include "python" "machine learning"
  python main.py --scrapers all --exclude "senior" "lead"
  python main.py --scrapers french-companies
  python main.py --scrapers data --debug
  python main.py --scrapers linkedin
        """,
    )

    parser.add_argument(
        "--scrapers",
        "-s",
        type=str,
        default="all",
        help="Scrapers to run (default: all)",
    )

    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode (default: False)"
    )

    parser.add_argument(
        "--verbosity",
        "-v",
        type=str,
        choices=["debug", "info", "warning"],
        default="info",
        help="Set the logging verbosity level (default: info)",
    )

    parser.add_argument(
        "--include",
        type=str,
        nargs="+",
        help="Additional keywords to include in job title filtering",
    )

    parser.add_argument(
        "--exclude",
        type=str,
        nargs="+",
        help="Additional keywords to exclude from job title filtering",
    )

    parser.add_argument(
        "--list-scrapers", action="store_true", help="List available scrapers and exit"
    )

    return parser


if __name__ == "__main__":  # noqa: C901
    # Parse command line arguments
    parser = create_parser()
    args = parser.parse_args()

    # Configure logging
    FORMAT = "%(message)s"

    # Determine log level based on verbosity and debug flags
    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
        }
        log_level = log_level_map[args.verbosity]

    logging.basicConfig(
        level=log_level, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )

    logger = logging.getLogger("vie-tracker")

    # Get scrapers configuration
    scrapers_config = get_scrapers_config()

    # Handle list-scrapers option
    if args.list_scrapers:
        logger.info(
            "[bold blue]Available Scrapers:[/bold blue]", extra={"markup": True}
        )
        for sid, config in scrapers_config.items():
            status = (
                "[green]enabled[/green]"
                if config.get("enabled", True)
                else "[red]disabled[/red]"
            )
            extra_info = ""
            if "keyword" in config:
                extra_info += f" (keyword: {config['keyword']})"
            if "location" in config:
                extra_info += f" (location: {config['location']})"
            logger.info(
                f"  {sid}: [bold]{config['name']}[/bold] - {status}",
                extra={"markup": True},
            )
            logger.info(f"      {config['description']}{extra_info}")
        exit(0)

    # Welcome message
    logger.info(
        "[bold magenta]🚀 VIE Job Tracker - Enhanced Edition[/bold magenta]",
        extra={"markup": True},
    )

    # Check environment variables
    DATABASE_ID = os.getenv("DATABASE_ID")
    NOTION_API = os.getenv("NOTION_API")

    if not DATABASE_ID or not NOTION_API:
        logger.error(
            "[red]❌ Error: DATABASE_ID and NOTION_API environment variables are required.[/red]",
            extra={"markup": True},
        )
        exit(1)

    try:
        # Parse scraper selection
        selected_scraper_ids = parse_scraper_selection(args.scrapers, scrapers_config)

        # Use default filters and add custom ones if provided
        include_filters, exclude_filters = get_default_filters()

        if args.include:
            include_filters.extend(args.include)
            logger.info(
                f"[green]Added custom include filters:[/green] {', '.join(args.include)}",
                extra={"markup": True},
            )

        if args.exclude:
            exclude_filters.extend(args.exclude)
            logger.info(
                f"[red]Added custom exclude filters:[/red] {', '.join(args.exclude)}",
                extra={"markup": True},
            )

        # Display configuration
        logger.info(
            f"[green]Selected scrapers ({len(selected_scraper_ids)}):[/green]",
            extra={"markup": True},
        )
        for sid in selected_scraper_ids:
            scraper_config = scrapers_config[sid]
            extra_info = ""
            if "keyword" in scraper_config:
                extra_info = f" (keyword: {scraper_config['keyword']})"
            if "location" in scraper_config:
                extra_info += f" (location: {scraper_config['location']})"

            # Show URL being scraped
            url_display = scraper_config.get("url", "N/A")
            if len(url_display) > 60:
                url_display = url_display[:57] + "..."

            logger.info(
                f"  • [bold]{scraper_config['name']}[/bold]{extra_info}",
                extra={"markup": True},
            )
            logger.info(f"    [dim]URL: {url_display}[/dim]", extra={"markup": True})

        logger.info(
            f"[green]Include filters:[/green] {len(include_filters)} keywords",
            extra={"markup": True},
        )
        if args.debug and include_filters:
            logger.debug(f"  {', '.join(include_filters)}")
        logger.info(
            f"[red]Exclude filters:[/red] {len(exclude_filters)} keywords",
            extra={"markup": True},
        )
        if args.debug and exclude_filters:
            logger.debug(f"  {', '.join(exclude_filters)}")
        logger.info(
            f"[yellow]Debug mode:[/yellow] {'Enabled' if args.debug else 'Disabled'}",
            extra={"markup": True},
        )

        # Initialize clients and processor
        logger.info(
            "[bold blue]🔧 Initializing services...[/bold blue]", extra={"markup": True}
        )
        notion_client = NotionClient(NOTION_API, DATABASE_ID)

        processor = OfferProcessor(
            notion_client=notion_client,
            selected_scrapers=selected_scraper_ids,
            include_filters=include_filters,
            exclude_filters=exclude_filters,
            debug=args.debug,
        )

        logger.info(
            "[bold blue]🕷️ Starting scraping and processing workflow...[/bold blue]",
            extra={"markup": True},
        )

        # Run the complete workflow
        scraped_offers = processor.scrape_and_process()

        if scraped_offers:
            logger.info(
                "[bold green]🎉 Workflow completed successfully![/bold green]",
                extra={"markup": True},
            )
            logger.info(
                f"[green]✅ Scraped and processed {len(scraped_offers)} total offers[/green]",
                extra={"markup": True},
            )
        else:
            logger.warning(
                "[yellow]⚠️ No offers found during scraping.[/yellow]",
                extra={"markup": True},
            )

    except ValueError as e:
        logger.error(f"[red]❌ Configuration error: {e}[/red]", extra={"markup": True})
        exit(1)
    except Exception as e:
        logger.error(
            f"[red]❌ Error during workflow: {e}[/red]", extra={"markup": True}
        )
        if args.debug:
            import traceback

            traceback.print_exc()
        exit(1)
