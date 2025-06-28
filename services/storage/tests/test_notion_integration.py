"""
Integration tests for NotionClient with JobOffer objects.

These tests require actual Notion API credentials and a test database.
Set the following environment variables:
- NOTION_API_TEST: Your Notion API token
- DATABASE_ID_TEST: Your test database ID

The test database should have the same schema as your production database.
"""

import os
from datetime import datetime
from unittest.mock import patch

import pytest

from services.scraping.src.base_model.job_offer import ContractType, JobOffer, JobSource
from services.storage.src.notion_integration import NotionClient


@pytest.fixture
def notion_client():
    """Create a NotionClient instance for testing."""
    notion_api = os.getenv("NOTION_API")
    database_id = os.getenv("DATABASE_ID_TEST")

    if not notion_api or not database_id:
        pytest.skip(
            "NOTION_API_TEST and DATABASE_ID_TEST environment variables required for integration tests"
        )

    return NotionClient(notion_api, database_id)


@pytest.fixture
def sample_job_offer():
    """Create a sample JobOffer for testing."""
    return JobOffer(
        title="Senior Software Engineer",
        company="Test Company",
        location="Paris, France",
        source=JobSource.BUSINESS_FRANCE,
        url="https://example.com/job/123",
        scraped_at=datetime.now(),
        contract_type=ContractType.VIE,
        salary="50,000 - 60,000 EUR",
        duration="24 months",
        reference="TEST-001",
        schedule_type="Full-time",
        job_content_description="A challenging role for a senior software engineer.",
    )


@pytest.fixture
def multiple_job_offers():
    """Create multiple JobOffer instances for batch testing."""
    offers = []

    # Offer 1: Air France
    offers.append(
        JobOffer(
            title="Data Analyst",
            company="Air France",
            location="Paris, France",
            source=JobSource.AIR_FRANCE,
            url="https://airfrance.com/job/456",
            scraped_at=datetime.now(),
            contract_type=ContractType.CDI,
            salary="45,000 EUR",
            duration="Permanent",
            reference="AF-456",
            schedule_type="Full-time",
            job_content_description="Analyze flight data and passenger trends.",
        )
    )

    # Offer 2: Apple
    offers.append(
        JobOffer(
            title="iOS Developer",
            company="Apple",
            location="Singapore",
            source=JobSource.APPLE,
            url="https://jobs.apple.com/job/789",
            scraped_at=datetime.now(),
            contract_type=ContractType.FULL_TIME,
            salary="80,000 USD",
            duration="Permanent",
            reference="APPLE-789",
            schedule_type="Full-time",
            job_content_description="Develop innovative iOS applications.",
        )
    )

    # Offer 3: Welcome to the Jungle
    offers.append(
        JobOffer(
            title="Product Manager",
            company="Startup Inc",
            location="Lyon, France",
            source=JobSource.WELCOME_TO_THE_JUNGLE,
            url="https://welcometothejungle.com/job/101",
            scraped_at=datetime.now(),
            contract_type=ContractType.CDI,
            salary="55,000 EUR",
            duration="Permanent",
            reference="WTTJ-101",
            schedule_type="Full-time",
            job_content_description="Lead product development and strategy.",
        )
    )

    return offers


class TestNotionClientIntegration:
    """Integration tests for NotionClient."""

    def test_client_initialization(self, notion_client):
        """Test that NotionClient initializes correctly without auto-loading offers."""
        assert notion_client.database_id is not None
        assert notion_client.client is not None
        # Verify that all_offers is not automatically loaded
        assert not hasattr(notion_client, "all_offers")

    def test_single_offer_does_not_exist_initially(
        self, notion_client, sample_job_offer
    ):
        """Test that a new offer doesn't exist in the database initially."""
        exists = notion_client.offer_exists(sample_job_offer)
        assert isinstance(exists, bool)
        # For a truly new offer, this should be False
        # Note: This might be True if the offer already exists from previous test runs

    def test_create_single_offer(self, notion_client, sample_job_offer):
        """Test creating a single job offer page."""
        # Clean up any existing offer with the same ID first
        self._cleanup_offer_by_id(notion_client, sample_job_offer.offer_id)

        # Verify it doesn't exist
        assert not notion_client.offer_exists(sample_job_offer)

        # Create the offer
        try:
            result = notion_client.create_page_from_job_offer(sample_job_offer)
        except Exception as e:
            pytest.fail(f"Failed to create job offer: {e}")

        # Verify creation was successful
        assert result is not None
        assert "id" in result

        # Verify it now exists
        assert notion_client.offer_exists(sample_job_offer)

    def test_create_duplicate_offer_is_skipped(self, notion_client, sample_job_offer):
        """Test that creating a duplicate offer is skipped."""
        # Ensure the offer exists (create it if it doesn't)
        if not notion_client.offer_exists(sample_job_offer):
            notion_client.create_page_from_job_offer(sample_job_offer)

        # Try to create it again - should be skipped
        result = notion_client.create_page_from_job_offer(sample_job_offer)
        assert result is None  # Should be None when skipped

    def test_batch_offer_existence_check(self, notion_client, multiple_job_offers):
        """Test batch checking of multiple offers."""
        # Clean up any existing offers first
        for offer in multiple_job_offers:
            self._cleanup_offer_by_id(notion_client, offer.offer_id)

        # Check existence of multiple offers
        existence_map = notion_client.offer_exists(multiple_job_offers)

        assert isinstance(existence_map, dict)
        assert len(existence_map) == len(multiple_job_offers)

        # All should be False initially
        for offer in multiple_job_offers:
            assert offer.offer_id in existence_map
            assert not existence_map[offer.offer_id]

    def test_batch_offer_creation(self, notion_client, multiple_job_offers):
        """Test batch creation of multiple offers."""
        # Clean up any existing offers first
        for offer in multiple_job_offers:
            self._cleanup_offer_by_id(notion_client, offer.offer_id)

        # Create multiple offers
        results = notion_client.create_pages_from_job_offers(multiple_job_offers)

        assert len(results) == len(multiple_job_offers)

        # All should have been created successfully
        for result in results:
            assert result is not None
            assert "id" in result

        # Verify all now exist
        existence_map = notion_client.offer_exists(multiple_job_offers)
        for offer in multiple_job_offers:
            assert existence_map[offer.offer_id]

    def test_batch_creation_with_existing_offers(
        self, notion_client, multiple_job_offers
    ):
        """Test batch creation where some offers already exist."""
        # Clean up all offers first
        for offer in multiple_job_offers:
            self._cleanup_offer_by_id(notion_client, offer.offer_id)

        # Create the first offer manually
        first_offer = multiple_job_offers[0]
        notion_client.create_page_from_job_offer(first_offer)

        # Now try to create all offers - first should be skipped
        results = notion_client.create_pages_from_job_offers(multiple_job_offers)

        assert len(results) == len(multiple_job_offers)
        assert results[0] is None  # First offer should be skipped

        # Other offers should be created
        for i in range(1, len(results)):
            assert results[i] is not None
            assert "id" in results[i]

    def test_get_all_offers_includes_offer_id(self, notion_client, sample_job_offer):
        """Test that get_all_offers includes the Offer ID field."""
        # Ensure we have at least one offer
        if not notion_client.offer_exists(sample_job_offer):
            notion_client.create_page_from_job_offer(sample_job_offer)

        # Get all offers
        offers = notion_client.get_all_offers()

        assert isinstance(offers, list)
        assert len(offers) > 0

        # Check that each offer has the expected fields including Offer ID
        for offer in offers:
            assert "Title" in offer
            assert "Company" in offer
            assert "Location" in offer
            assert "Source" in offer
            assert "URL" in offer
            assert "Offer ID" in offer

        # Find our test offer
        test_offer = next(
            (
                offer
                for offer in offers
                if offer["Offer ID"] == sample_job_offer.offer_id
            ),
            None,
        )
        assert test_offer is not None
        assert test_offer["Title"] == sample_job_offer.title
        assert test_offer["Company"] == sample_job_offer.company

    def test_offer_id_uniqueness(self, notion_client):
        """Test that offers with same content generate the same ID."""
        # Create two identical offers
        offer1 = JobOffer(
            title="Identical Job",
            company="Same Company",
            location="Same Location",
            source=JobSource.BUSINESS_FRANCE,
            url="https://same-url.com/job",
            scraped_at=datetime.now(),  # Different timestamps
        )

        offer2 = JobOffer(
            title="Identical Job",
            company="Same Company",
            location="Same Location",
            source=JobSource.BUSINESS_FRANCE,
            url="https://same-url.com/job",
            scraped_at=datetime.now(),  # Different timestamps
        )

        # They should have the same offer ID
        assert offer1.offer_id == offer2.offer_id

        # Only one should be created
        self._cleanup_offer_by_id(notion_client, offer1.offer_id)

        result1 = notion_client.create_page_from_job_offer(offer1)
        result2 = notion_client.create_page_from_job_offer(offer2)

        assert result1 is not None
        assert result2 is None  # Should be skipped as duplicate

    def test_notion_format_conversion(self, sample_job_offer):
        """Test that JobOffer converts correctly to Notion format."""
        notion_properties = sample_job_offer.to_notion_format()

        # Verify required fields
        assert "Title" in notion_properties
        assert "Company" in notion_properties
        assert "Location" in notion_properties
        assert "Source" in notion_properties
        assert "URL" in notion_properties
        assert "Offer ID" in notion_properties

        # Verify structure
        assert (
            notion_properties["Title"]["title"][0]["text"]["content"]
            == sample_job_offer.title
        )
        assert (
            notion_properties["Company"]["select"]["name"] == sample_job_offer.company
        )
        assert notion_properties["Source"]["select"]["name"] == sample_job_offer.source
        assert notion_properties["URL"]["url"] == sample_job_offer.url
        assert (
            notion_properties["Offer ID"]["rich_text"][0]["text"]["content"]
            == sample_job_offer.offer_id
        )

    def _cleanup_offer_by_id(self, notion_client, offer_id):
        """Helper method to clean up an offer by its ID."""
        try:
            # Query for the offer
            query = {
                "database_id": notion_client.database_id,
                "filter": {"property": "Offer ID", "rich_text": {"equals": offer_id}},
            }
            response = notion_client.client.databases.query(**query)

            # Archive any found pages
            for page in response.get("results", []):
                page_id = page.get("id")
                if page_id:
                    notion_client.client.pages.update(page_id, archived=True)
        except Exception as e:
            # Ignore cleanup errors
            print(f"Warning: Could not cleanup offer {offer_id}: {e}")


class TestNotionClientEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_offer_list(self, notion_client):
        """Test behavior with empty offer list."""
        result = notion_client.offer_exists([])
        assert result == {}

        result = notion_client.create_pages_from_job_offers([])
        assert result == []

    def test_offer_with_long_description(self, notion_client):
        """Test offer with description longer than Notion's limit."""
        long_description = "A" * 3000  # Longer than 2000 char limit

        offer = JobOffer(
            title="Job with Long Description",
            company="Test Company",
            location="Test Location",
            source=JobSource.BUSINESS_FRANCE,
            url="https://example.com/long-desc",
            scraped_at=datetime.now(),
            job_content_description=long_description,
        )

        # Should be able to create the offer (job_content_description is no longer in Notion format)
        notion_props = offer.to_notion_format()
        # Verify the main properties are there
        assert "Title" in notion_props
        assert "Company" in notion_props
        assert "Location" in notion_props

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_environment_variables(self):
        """Test behavior when environment variables are missing."""
        with pytest.raises(
            ValueError,
            match="Both notion_api_key and database_id must be provided and non-empty",
        ):
            # Should fail to create client without proper env vars
            NotionClient("", "")

    def test_check_multiple_offers_exist_method(
        self, notion_client, multiple_job_offers
    ):
        """Test the _check_multiple_offers_exist method directly with database filtering."""
        # Clean up any existing offers first
        for offer in multiple_job_offers:
            self._cleanup_offer_by_id(notion_client, offer.offer_id)

        # Test with no offers existing
        offer_ids = [offer.offer_id for offer in multiple_job_offers]
        existence_map = notion_client._check_multiple_offers_exist(offer_ids)

        assert isinstance(existence_map, dict)
        assert len(existence_map) == len(offer_ids)
        for offer_id in offer_ids:
            assert offer_id in existence_map
            assert not existence_map[offer_id]  # Should all be False initially

        # Create the first two offers
        notion_client.create_page_from_job_offer(multiple_job_offers[0])
        notion_client.create_page_from_job_offer(multiple_job_offers[1])

        # Test with some offers existing
        existence_map = notion_client._check_multiple_offers_exist(offer_ids)

        assert existence_map[multiple_job_offers[0].offer_id] is True
        assert existence_map[multiple_job_offers[1].offer_id] is True
        assert existence_map[multiple_job_offers[2].offer_id] is False

        # Test with single offer ID (edge case)
        single_offer_map = notion_client._check_multiple_offers_exist(
            [multiple_job_offers[0].offer_id]
        )
        assert len(single_offer_map) == 1
        assert single_offer_map[multiple_job_offers[0].offer_id] is True

        # Test with empty list
        empty_map = notion_client._check_multiple_offers_exist([])
        assert empty_map == {}

        # Test with non-existent offer IDs
        fake_ids = ["99999", "88888", "77777"]
        fake_map = notion_client._check_multiple_offers_exist(fake_ids)
        assert len(fake_map) == 3
        for fake_id in fake_ids:
            assert fake_map[fake_id] is False

    def _cleanup_offer_by_id(self, notion_client, offer_id):
        """Helper method to clean up an offer by its ID."""
        try:
            # Query for the offer
            query = {
                "database_id": notion_client.database_id,
                "filter": {"property": "Offer ID", "rich_text": {"equals": offer_id}},
            }
            response = notion_client.client.databases.query(**query)

            # Archive any found pages
            for page in response.get("results", []):
                page_id = page.get("id")
                if page_id:
                    notion_client.client.pages.update(page_id, archived=True)
        except Exception as e:
            # Ignore cleanup errors
            print(f"Warning: Could not cleanup offer {offer_id}: {e}")


if __name__ == "__main__":
    # Run tests with: python -m pytest services/storage/tests/test_notion_integration.py -v
    pytest.main([__file__, "-v", "-s"])
