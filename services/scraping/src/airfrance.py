import logging
import warnings
from datetime import datetime
from typing import List, Optional

from services.scraping.src.base_model.job_offer import (
    ContractType,
    JobOfferInput,
    JobSource,
    generate_job_offer_id,
)
from services.scraping.src.base_model.job_scraper_base import JobScraperBase
from services.storage.src.notion_integration import NotionClient


class AirFranceJobScraper(JobScraperBase):
    """Air France Job Scraper using Playwright and Pydantic models."""

    def __init__(
        self,
        url: str,
        notion_client: NotionClient,
        keyword: str = "",
        contract_type: str = "",
        include_filters: Optional[List[str]] = None,
        exclude_filters: Optional[List[str]] = None,
        debug: bool = False,
        headless: bool = True,
    ):
        super().__init__(
            url=url,
            include_filters=include_filters,
            exclude_filters=exclude_filters,
            debug=debug,
            headless=headless,
            _offers_urls=[],
            notion_client=notion_client,
        )
        self.keyword = keyword
        self.contract_type = contract_type
        self.notion_client = notion_client
        self._offers_urls = []
        self.total_offers = 0
        self.notion_client = notion_client
        self.logger = logging.getLogger("job-tracker.airfrance-scraper")

    async def extract_all_offers_url(self) -> None:  # noqa: C901
        """
        Load all offers by navigating through pagination and applying filters.
        """
        if not self.page:
            raise RuntimeError("Page not initialized")

        try:
            await self.page.goto(self.url)
            await self.wait_random(2, 4)

            # Handle cookies
            try:
                cookie_btn = self.page.locator("#didomi-notice-agree-button")
                if await cookie_btn.count() > 0:
                    await cookie_btn.click()
                    await self.wait_random(1, 2)
                    await self.page.reload()
            except Exception:
                pass

            # Apply keyword filter
            if self.keyword == "":
                self.logger.warning("No keyword provided. Skipping keyword filtering.")
            else:
                try:
                    # Wait for the keyword input to be available
                    keyword_input = self.page.locator(
                        "input[name*='OfferCriteria_Keywords']"
                    )
                    await keyword_input.wait_for(timeout=10000)

                    # Clear and fill the input field
                    await keyword_input.clear()
                    await keyword_input.fill(self.keyword)

                    # Alternative: Use JavaScript if direct interaction fails
                    await self.page.evaluate(
                        f"""
                        var input = document.querySelector("input[name*='OfferCriteria_Keywords']");
                        if (input) {{
                            input.value = "{self.keyword}";
                            var event = new Event('input', {{ bubbles: true }});
                            input.dispatchEvent(event);
                        }}
                        """
                    )

                    self.logger.info(f"Applied keyword filter: {self.keyword}")
                    await self.wait_random(1, 2)

                except Exception as e:
                    await self.save_error_screenshot("airfrance-keyword-error")
                    self.logger.warning(f"Could not apply keyword filter: {e}")

            if self.contract_type == "":
                self.logger.warning(
                    "No contract type provided. Skipping contract type filtering."
                )
            else:
                try:
                    # Use JavaScript to set the contract type value, similar to the keyword filter
                    await self.page.evaluate(
                        f"""
                        var select = document.querySelector("#ctl00_ctl00_moteurRapideOffre_ctl00_EngineCriteriaCollection_Contract");
                        if (select) {{
                            select.value = "{self.contract_type}";
                            var event = new Event('change', {{ bubbles: true }});
                            select.dispatchEvent(event);
                        }}
                        """
                    )
                except Exception as e:
                    await self.save_error_screenshot("airfrance-contract-type-error")
                    self.logger.warning(f"Could not apply contract type filter: {e}")

            # Submit search
            try:
                search_btn = self.page.locator(
                    "#ctl00_ctl00_moteurRapideOffre_BT_recherche"
                )
                await search_btn.click()
                await self.wait_random(2, 4)
                self.logger.info("Offers Filtered.")
            except Exception as e:
                await self.save_error_screenshot("airfrance-search-error")
                self.logger.warning(f"Could not submit search: {e}")

            # Get total offers count
            try:
                count_element = self.page.locator(
                    "#ctl00_ctl00_corpsRoot_corps_PaginationLower_TotalOffers"
                )
                await count_element.wait_for(timeout=15000)
                count_text = await count_element.text_content()
                if count_text:
                    self.total_offers = int(count_text.split()[0])
                    self.logger.info(f"Total offers found: {self.total_offers}")
                else:
                    self.total_offers = 0
            except Exception as e:
                await self.save_error_screenshot("airfrance-count-error")
                self.logger.warning(f"Could not determine total offers: {e}")
                self.total_offers = 0

            # Navigate through pages and collect offer URLs
            while True:
                try:
                    # Wait for offers to load
                    await self.page.locator(".ts-offer-list-item").first.wait_for(
                        timeout=10000
                    )

                    # Extract offer URLs from current page
                    offer_elements = self.page.locator(".ts-offer-list-item")
                    offer_count = await offer_elements.count()

                    for i in range(offer_count):
                        offer = offer_elements.nth(i)
                        try:
                            title_link = offer.locator(
                                ".ts-offer-list-item__title-link"
                            )
                            title = await title_link.text_content()
                            url = await title_link.get_attribute("href")

                            if title and self.filter_job_title(
                                job_title=title.strip(),
                                include_filters=self.include_filters,
                                exclude_filters=self.exclude_filters,
                            ):
                                continue

                            if url:
                                url = "https://recrutement.airfrance.com/" + url
                                self._offers_urls.append(
                                    {
                                        "url": url,
                                        "id": generate_job_offer_id(
                                            company="Air France", url=url, title=title
                                        ),
                                    }
                                )

                        except Exception as e:
                            self.logger.debug(f"Error extracting offer {i}: {e}")

                    self.logger.debug(f"{offer_count} offers loaded")

                    # Try to navigate to next page
                    try:
                        next_button = self.page.locator(
                            "#ctl00_ctl00_corpsRoot_corps_Pagination_linkSuivPage"
                        )
                        if (
                            await next_button.count() > 0
                            and await next_button.is_enabled()
                        ):
                            await next_button.click()
                            await self.wait_random(1, 3)
                            # Wait for new page to load
                            await self.page.locator(
                                ".ts-offer-list-item"
                            ).first.wait_for(timeout=10000)
                        else:
                            self.logger.info(
                                "Reached last page or next button not available"
                            )
                            break
                    except Exception:
                        self.logger.info(
                            "Reached last page or could not find next button"
                        )
                        break

                except Exception as e:
                    self.logger.error(f"Error loading offers: {e}")
                    break

        except Exception as e:
            raise ValueError(f"Error loading offers: {str(e)}")

        self.logger.info("Finished loading all available offers.")
        self.logger.info(f"Total after filters : {len(self._offers_urls)}")

    async def parse_offers(self) -> List[JobOfferInput]:  # noqa: C901
        """
        Extract offers data from the collected URLs.

        Returns:
            List[JobOfferInput]: A list of JobOfferInput objects containing offer details.
        """
        if not self.page:
            raise RuntimeError("Page not initialized")

        offers = []

        for offer in self._offers_urls:
            try:
                await self.page.goto(offer["url"])
                await self.wait_random(1, 3)

                # Extract offer data
                title = await self._safe_get_text(
                    "h1.ts-offer-page__title span:first-child", "N/A"
                )

                reference = await self._safe_get_text(
                    ".ts-offer-page__reference", "N/A"
                )
                if reference != "N/A" and "Référence" in reference:
                    reference = reference.split("Référence")[-1].strip()

                contract_type_text = await self._safe_get_text(
                    "#fldjobdescription_contract", "N/A"
                )
                duration = await self._safe_get_text(
                    "#fldjobdescription_contractlength", "N/A"
                )

                location_text = await self._safe_get_text(
                    "#fldlocation_location_geographicalareacollection", "N/A"
                )
                location = (
                    location_text.split(",")[-1] if location_text != "N/A" else "N/A"
                )

                # Extract company from image alt text
                company = "Air France"
                try:
                    company_img = self.page.locator(
                        "div.ts-offer-page__entity-logo img"
                    )
                    if await company_img.count() > 0:
                        alt_text = await company_img.get_attribute("alt")
                        if alt_text and " - " in alt_text:
                            company = alt_text.split(" - ")[-1].strip()
                except Exception:
                    pass

                # job_category = await self._safe_get_text("#fldjobdescription_professionalcategory", "N/A")
                schedule_type = await self._safe_get_text(
                    "#fldjobdescription_customcodetablevalue3", "N/A"
                )
                # job_type = await self._safe_get_text("#fldjobdescription_primaryprofile", "N/A")

                # Combine description parts
                desc_parts = []
                desc1 = await self._safe_get_text("#fldjobdescription_longtext1")
                desc2 = await self._safe_get_text("#fldjobdescription_description1")

                if desc1 and desc1 != "N/A":
                    desc_parts.append(desc1)
                if desc2 and desc2 != "N/A":
                    desc_parts.append(desc2)

                description = "\n".join(desc_parts) if desc_parts else "N/A"

                # Map contract type to enum
                contract_type = ContractType.CDI
                if contract_type_text and contract_type_text != "N/A":
                    contract_type_lower = contract_type_text.lower()
                    if "cdd" in contract_type_lower:
                        contract_type = ContractType.CDD
                    elif (
                        "stage" in contract_type_lower
                        or "intern" in contract_type_lower
                    ):
                        contract_type = ContractType.INTERNSHIP
                    elif "freelance" in contract_type_lower:
                        contract_type = ContractType.FREELANCE

                offer_input = JobOfferInput(
                    title=title,
                    company=company,
                    location=location,
                    contract_type=contract_type,
                    duration=duration,
                    schedule_type=schedule_type,
                    job_content_description=description,
                    reference=reference,
                    source=JobSource.AIR_FRANCE,
                    url=offer["url"],
                    scraped_at=datetime.utcnow(),
                )

                offers.append(offer_input)
                if self.debug:
                    self.logger.debug(
                        f"Air France offer extracted: {title} at {company}"
                    )

            except Exception as e:
                warnings.warn(f"Error extracting data for offer {offer['url']}: {e}")

        return offers


if __name__ == "__main__":
    import os

    DATABASE_ID = os.getenv("DATABASE_ID")
    NOTION_API = os.getenv("NOTION_API")
    assert DATABASE_ID, "DATABASE_ID environment variable is not set."
    assert NOTION_API, "NOTION_API environment variable is not set."
    notion_client = NotionClient(NOTION_API, DATABASE_ID)
    scraper = AirFranceJobScraper(
        url="https://recrutement.airfrance.com/offre-de-emploi/liste-offres.aspx/",
        keyword="data",
        contract_type="CDI",
        include_filters=["data", "engineer", "software"],
        exclude_filters=["stage", "alternance", "apprenti"],
        debug=True,
        headless=False,
        notion_client=notion_client,
    )
    offers = scraper.scrape()
    scraper.logger.info(offers)
