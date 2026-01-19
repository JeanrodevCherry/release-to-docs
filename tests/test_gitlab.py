import pytest
from unittest.mock import AsyncMock
from src.gitlab import GitLabClient
from src.models import Issue, Release

@pytest.fixture
def mock_gitlab_client():
    return GitLabClient(
        api_url="https://gitlab.com/api/v4",
        token="test_token",
        project_id=123
    )

import pytest
from unittest.mock import AsyncMock, Mock
from src.gitlab import GitLabClient
from src.models import Issue, Release

@pytest.fixture
def mock_gitlab_client():
    return GitLabClient(
        api_url="https://gitlab.com/api/v4",
        token="test_token",
        project_id=123
    )

@pytest.mark.asyncio
async def test_get_release(mock_gitlab_client):
    mock_response = {
        "tag_name": "v1.0.0",
        "name": "Version 1.0.0",
        "description": "Fixes #123 and adds #456",
        "created_at": "2023-01-01T00:00:00Z",
        "released_at": "2023-01-01T00:00:00Z"
    }
    mock_response_obj = Mock()
    mock_response_obj.raise_for_status = Mock()
    mock_response_obj.json = Mock(return_value=mock_response)
    mock_gitlab_client.client.get = AsyncMock(return_value=mock_response_obj)

    release = await mock_gitlab_client.get_release("v1.0.0")
    assert release["tag_name"] == "v1.0.0"

@pytest.mark.asyncio
async def test_get_issue(mock_gitlab_client):
    mock_response = {
        "id": 123,
        "title": "Fix bug",
        "description": "Bug description",
        "state": "closed",
        "labels": ["bug"],
        "assignee": {"name": "John Doe"},
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
    }
    mock_response_obj = Mock()
    mock_response_obj.raise_for_status = Mock()
    mock_response_obj.json = Mock(return_value=mock_response)
    mock_gitlab_client.client.get = AsyncMock(return_value=mock_response_obj)

    issue = await mock_gitlab_client.get_issue(123)
    assert issue["id"] == 123

def test_extract_issue_ids(mock_gitlab_client):
    description = "This release fixes #123 and adds #456, also closes #789"
    ids = mock_gitlab_client.extract_issue_ids(description)
    assert ids == [123, 456, 789]

@pytest.mark.asyncio
async def test_fetch_release_with_issues(mock_gitlab_client):
    # Mock release
    release_mock = {
        "tag_name": "v1.0.0",
        "name": "Version 1.0.0",
        "description": "Fixes #123",
        "created_at": "2023-01-01T00:00:00Z",
        "released_at": "2023-01-01T00:00:00Z"
    }
    # Mock issue
    issue_mock = {
        "id": 123,
        "title": "Fix bug",
        "description": "Bug description",
        "state": "closed",
        "labels": ["bug"],
        "assignee": {"name": "John Doe"},
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
    }

    release_resp = Mock()
    release_resp.raise_for_status = Mock()
    release_resp.json = Mock(return_value=release_mock)
    issue_resp = Mock()
    issue_resp.raise_for_status = Mock()
    issue_resp.json = Mock(return_value=issue_mock)

    mock_gitlab_client.client.get = AsyncMock(side_effect=[release_resp, issue_resp])

    release = await mock_gitlab_client.fetch_release_with_issues("v1.0.0")
    assert release.tag_name == "v1.0.0"
    assert len(release.issues) == 1
    assert release.issues[0].id == 123