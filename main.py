import argparse
import os
from typing import Dict, List

from rich.console import Console

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
        return ["2", "3", "4", "5"]
    elif selection in ["tech", "technology"]:
        return ["3", "4", "5"]
    elif selection in ["wttj", "welcome-to-the-jungle"]:
        return ["4", "5"]
    elif selection in ["airfrance", "air-france"]:
        return ["2"]
    elif selection == "apple":
        return ["3"]
    elif selection in ["data", "data-engineer", "dataengineer"]:
        return ["4"]
    elif selection in ["ai", "artificial-intelligence"]:
        return ["5"]
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
  all               - Run all scrapers (1,2,3,4,5)
  vie               - VIE-focused scrapers (1) [alias: business-france, businessfrance]
  cdi               - CDI-focused scrapers (2,3,4,5)
  tech              - Tech company scrapers (3,4,5) [alias: technology]
  wttj              - Welcome to the Jungle scrapers (4,5) [alias: welcome-to-the-jungle]
  french-companies  - French companies (1,2) [alias: france]
  airfrance         - Air France only (2) [alias: air-france]
  apple             - Apple only (3)
  data              - Data Engineer roles (4) [alias: data-engineer, dataengineer]
  ai                - AI roles (5) [alias: artificial-intelligence]
  1,3,5             - Specific scrapers by ID (comma-separated)

Available Scrapers:
  1 - Business France (VIE)
  2 - Air France
  3 - Apple
  4 - Welcome to the Jungle (Data Engineer)
  5 - Welcome to the Jungle (AI)

Examples:
  python main.py --scrapers all
  python main.py --scrapers vie --debug
  python main.py --scrapers apple
  python main.py --scrapers 1,3,5
  python main.py --list-scrapers
  python main.py --scrapers tech --include "python" "machine learning"
  python main.py --scrapers all --exclude "senior" "lead"
  python main.py --scrapers french-companies
  python main.py --scrapers data --debug
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
    console = Console()

    # Parse command line arguments
    parser = create_parser()
    args = parser.parse_args()

    # Get scrapers configuration
    scrapers_config = get_scrapers_config()

    # Handle list-scrapers option
    if args.list_scrapers:
        console.print("\n[bold blue]Available Scrapers:[/bold blue]")
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
            console.print(f"  {sid}: [bold]{config['name']}[/bold] - {status}")
            console.print(f"      {config['description']}{extra_info}")
        exit(0)

    # Welcome message
    console.print(
        "\n[bold magenta]🚀 VIE Job Tracker - Enhanced Edition[/bold magenta]"
    )

    # Check environment variables
    DATABASE_ID = os.getenv("DATABASE_ID")
    NOTION_API = os.getenv("NOTION_API")

    if not DATABASE_ID or not NOTION_API:
        console.print(
            "[red]❌ Error: DATABASE_ID and NOTION_API environment variables are required.[/red]"
        )
        exit(1)

    try:
        # Parse scraper selection
        selected_scraper_ids = parse_scraper_selection(args.scrapers, scrapers_config)

        # Use default filters and add custom ones if provided
        include_filters, exclude_filters = get_default_filters()

        if args.include:
            include_filters.extend(args.include)
            console.print(
                f"[green]Added custom include filters:[/green] {', '.join(args.include)}"
            )

        if args.exclude:
            exclude_filters.extend(args.exclude)
            console.print(
                f"[red]Added custom exclude filters:[/red] {', '.join(args.exclude)}"
            )

        # Display configuration
        console.print(
            f"\n[green]Selected scrapers ({len(selected_scraper_ids)}):[/green]"
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

            console.print(f"  • [bold]{scraper_config['name']}[/bold]{extra_info}")
            console.print(f"    [dim]URL: {url_display}[/dim]")

        console.print(
            f"\n[green]Include filters:[/green] {len(include_filters)} keywords"
        )
        if args.debug and include_filters:
            console.print(f"  {', '.join(include_filters)}")
        console.print(f"[red]Exclude filters:[/red] {len(exclude_filters)} keywords")
        if args.debug and exclude_filters:
            console.print(f"  {', '.join(exclude_filters)}")
        console.print(
            f"[yellow]Debug mode:[/yellow] {'Enabled' if args.debug else 'Disabled'}"
        )

        # Initialize clients and processor
        console.print("\n[bold blue]🔧 Initializing services...[/bold blue]")
        notion_client = NotionClient(NOTION_API, DATABASE_ID)

        processor = OfferProcessor(
            notion_client=notion_client,
            selected_scrapers=selected_scraper_ids,
            include_filters=include_filters,
            exclude_filters=exclude_filters,
            debug=args.debug,
        )

        console.print(
            "\n[bold blue]🕷️ Starting scraping and processing workflow...[/bold blue]"
        )

        # Run the complete workflow
        scraped_offers = processor.scrape_and_process()

        if scraped_offers:
            console.print(
                "\n[bold green]🎉 Workflow completed successfully![/bold green]"
            )
            console.print(
                f"[green]✅ Scraped and processed {len(scraped_offers)} total offers[/green]"
            )
        else:
            console.print("\n[yellow]⚠️ No offers found during scraping.[/yellow]")

    except ValueError as e:
        console.print(f"\n[red]❌ Configuration error: {e}[/red]")
        exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Error during workflow: {e}[/red]")
        if args.debug:
            import traceback

            traceback.print_exc()
        exit(1)
