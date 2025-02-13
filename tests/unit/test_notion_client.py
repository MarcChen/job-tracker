from unittest.mock import patch

import pytest

from src.notion_integration import NotionClient


@pytest.fixture
def notion_client():
    with patch.object(NotionClient, "get_all_offers", return_value=[]):
        nc = NotionClient(notion_api_key="fake_api_key", database_id="fake_database_id")
    # Override offers to prevent automatic API calls.
    nc.all_offers = []
    return nc


def test_offer_exists(notion_client):
    # Set up an offer to simulate an existing page.
    notion_client.all_offers = [
        {
            "Title": "Test Title",
            "Company": "Fake Company",
            "Location": "Fake Location",
            "Source": "Fake Source",
            "URL": ""
        }
    ]
    # Duplicate offer; note location is no longer used.
    assert notion_client.offer_exists("Test Title", "Fake Source", company="Fake Company") is True
    # Nonexistent offer.
    assert notion_client.offer_exists("Nonexistent Title", "Fake Source", company="Fake Company") is False


@patch("src.notion_integration.NotionClient.create_page")
def test_create_page(mock_create, notion_client):
    # Ensure no duplicate exists.
    notion_client.all_offers = []
    # Configure the mock to simulate page creation.
    mock_create.return_value = {"id": "new_page_id"}
    properties = {
        "Title": {"title": [{"text": {"content": "New Title"}}]},
        "Company": {"select": {"name": "Tech Corp"}},
        "Location": {"select": {"name": "Remote"}},  # remains in properties if needed
        "Source": {"select": {"name": "JobBoard"}},
        "URL": {"url": "http://example.com"}
    }
    response = notion_client.create_page(properties)
    assert response is not None
    assert response["id"] == "new_page_id"
