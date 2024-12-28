import pytest
from unittest.mock import patch, MagicMock
from notion_client import NotionClient 


@pytest.fixture
def notion_client():
    return NotionClient(notion_api_key="fake_api_key", database_id="fake_database_id")


@patch("notion_client.requests.post")
def test_title_exists(mock_post, notion_client):
    # Mock response from Notion API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {"properties": {"Title": {"title": [{"text": {"content": "Test Title"}}]}}}
        ]
    }
    mock_post.return_value = mock_response

    # Test for existing title
    assert notion_client.title_exists("Test Title") is True

    # Test for non-existing title
    assert notion_client.title_exists("Nonexistent Title") is False


@patch("notion_client.requests.post")
def test_create_page(mock_post, notion_client):
    # Mock response for title existence check
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {"results": []})

    # Mock response for page creation
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {"id": "new_page_id"})

    properties = {
        "Title": {"title": [{"text": {"content": "New Title"}}]},
        "Candidates": {"number": 5},
        "Views": {"number": 100},
        "ContractType": {"select": {"name": "Full-Time"}},
        "Company": {"select": {"name": "Tech Corp"}},
        "Location": {"select": {"name": "Remote"}},
        "Duration": {"select": {"name": "6 months"}}
    }

    response = notion_client.create_page(properties)
    assert response is not None
    assert response["id"] == "new_page_id"
