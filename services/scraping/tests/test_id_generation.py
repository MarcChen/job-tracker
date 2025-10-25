import sys
from datetime import datetime

from services.scraping.src.base_model.job_offer import (
    JobOffer,
    JobOfferInput,
    JobSource,
    generate_job_offer_id,
)


def test_standalone_id_generation():
    """Test the standalone ID generation function."""
    print("=== Testing Standalone ID Generation ===")

    # Test with sample data
    company = "Apple Inc."
    title = "Software Engineer"
    url = "https://jobs.apple.com/123"

    id1 = generate_job_offer_id(company, title, url)
    print(f"Generated ID: {id1}")

    # Test that same inputs produce same ID
    id2 = generate_job_offer_id(company, title, url)
    print(f"Generated ID (repeat): {id2}")
    assert id1 == id2, "Same inputs should produce same ID"

    # Test that different inputs produce different IDs
    id3 = generate_job_offer_id("Different Company", title, url)
    print(f"Generated ID (different company): {id3}")
    assert id1 != id3, "Different inputs should produce different IDs"

    # Test with whitespace and case variations
    id4 = generate_job_offer_id(
        "  APPLE INC.  ", "  SOFTWARE ENGINEER  ", "  HTTPS://JOBS.APPLE.COM/123  "
    )
    print(f"Generated ID (with whitespace/case): {id4}")
    assert id1 == id4, "Normalization should handle whitespace and case"

    print("✅ Standalone ID generation tests passed!")


def test_job_offer_auto_id():
    """Test automatic ID generation in JobOffer class."""
    print("\n=== Testing JobOffer Auto ID Generation ===")

    # Create a JobOffer without specifying offer_id
    job = JobOffer(
        title="Data Scientist",
        company="TechCorp",
        location="Paris, France",
        source=JobSource.BUSINESS_FRANCE,
        url="https://example.com/job/456",
        scraped_at=datetime.now(),
    )

    print(f"Auto-generated ID: {job.offer_id}")
    assert len(job.offer_id) == 5, "ID should be 5 digits long"
    assert job.offer_id.isdigit(), "ID should contain only digits"

    # Test regenerate_id method
    original_id = job.offer_id
    new_id = job.regenerate_id()

    print(f"Regenerated ID: {new_id}")
    assert new_id == original_id, "Regenerated ID should be the same for same data"
    assert job.offer_id == new_id, "Instance ID should be updated"

    # Test that changing data produces different ID
    job.title = "Senior Data Scientist"
    regenerated_id = job.regenerate_id()
    print(f"ID after title change: {regenerated_id}")
    assert regenerated_id != original_id, "Changing data should produce different ID"

    print("✅ JobOffer auto ID generation tests passed!")


def test_job_offer_input():
    """Test ID generation through JobOfferInput."""
    print("\n=== Testing JobOfferInput to JobOffer Conversion ===")

    # Create input with raw data
    input_data = JobOfferInput(
        title="  Machine Learning Engineer  ",
        company="Google",
        location="Mountain View",
        source=JobSource.APPLE,  # This will be normalized
        url="https://careers.google.com/123",
        scraped_at=datetime.now(),
        contract_type=None,
        salary="120k-150k USD",
    )

    # Convert to validated JobOffer
    job = input_data.to_job_offer()

    print(f"Generated ID from input: {job.offer_id}")
    assert len(job.offer_id) == 5, "ID should be 5 digits long"
    assert job.offer_id.isdigit(), "ID should contain only digits"

    print("✅ JobOfferInput conversion tests passed!")


def test_notion_format():
    """Test that Notion format includes the offer_id."""
    print("\n=== Testing Notion Format with Offer ID ===")

    job = JobOffer(
        title="DevOps Engineer",
        company="StartupXYZ",
        location="Berlin, Germany",
        source=JobSource.WELCOME_TO_THE_JUNGLE,
        url="https://startup.com/jobs/789",
    )

    notion_data = job.to_notion_format()

    print(
        f"Offer ID in Notion format: {notion_data['Offer ID']['rich_text'][0]['text']['content']}"
    )
    assert "Offer ID" in notion_data, "Notion format should include Offer ID"
    assert notion_data["Offer ID"]["rich_text"][0]["text"]["content"] == job.offer_id, (
        "Notion format should match job offer_id"
    )

    print("✅ Notion format tests passed!")


def test_legacy_format():
    """Test that legacy format includes the offer_id."""
    print("\n=== Testing Legacy Format with Offer ID ===")

    job = JobOffer(
        title="Frontend Developer",
        company="WebCorp",
        location="London, UK",
        source=JobSource.AIR_FRANCE,
        url="https://webcorp.com/careers/101",
    )

    legacy_data = job.to_legacy_dict()

    print(f"Offer ID in legacy format: {legacy_data['Offer ID']}")
    assert "Offer ID" in legacy_data, "Legacy format should include Offer ID"
    assert legacy_data["Offer ID"] == job.offer_id, (
        "Legacy format should match job offer_id"
    )

    print("✅ Legacy format tests passed!")


def test_id_generation_with_none_url():
    """Test ID generation when URL is None."""
    print("\n=== Testing ID Generation with None URL ===")

    # Test with None URL
    company = "Apple Inc."
    title = "Software Engineer"

    id1 = generate_job_offer_id(company, title, None)
    print(f"Generated ID with None URL: {id1}")
    assert len(id1) == 5, "ID should be 5 digits long"
    assert id1.isdigit(), "ID should contain only digits"

    # Test that same inputs with None URL produce same ID
    id2 = generate_job_offer_id(company, title, None)
    print(f"Generated ID with None URL (repeat): {id2}")
    assert id1 == id2, "Same inputs with None URL should produce same ID"

    # Test that None URL and empty string URL produce same ID
    id3 = generate_job_offer_id(company, title, "")
    print(f"Generated ID with empty string URL: {id3}")
    assert id1 == id3, "None URL and empty string URL should produce same ID"

    # Test that None URL produces different ID than actual URL
    id4 = generate_job_offer_id(company, title, "https://jobs.apple.com/123")
    print(f"Generated ID with actual URL: {id4}")
    assert id1 != id4, "None URL and actual URL should produce different IDs"

    # Test with default parameter (not passing URL at all)
    id5 = generate_job_offer_id(company, title)
    print(f"Generated ID with default URL parameter: {id5}")
    assert id1 == id5, "None URL and default parameter should produce same ID"

    print("✅ ID generation with None URL tests passed!")


if __name__ == "__main__":
    print("Testing Job Offer ID Generation System\n")

    try:
        test_standalone_id_generation()
        test_job_offer_auto_id()
        test_job_offer_input()
        test_notion_format()
        test_legacy_format()
        test_id_generation_with_none_url()

        print("\n🎉 All tests passed! ID generation system is working correctly.")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
