import httpx
import re
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Dict, Any
from loguru import logger
from .models import Issue, Release, MergeRequest


class GitLabClient:
    def __init__(
        self, api_url: str, token: str, project_id: int, timeout: float = 30.0
    ):
        self.api_url = api_url.rstrip("/")
        self.token = token
        self.project_id = project_id
        self.client = httpx.AsyncClient(
            headers={"PRIVATE-TOKEN": token}, timeout=timeout
        )

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_release(self, tag_name: str) -> Dict[str, Any]:
        url = f"{self.api_url}/projects/{self.project_id}/releases/{tag_name}"
        logger.info(f"Fetching release {tag_name} from {url}")
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_issue(self, issue_id: int) -> Dict[str, Any]:
        url = f"{self.api_url}/projects/{self.project_id}/issues/{issue_id}"
        logger.info(f"Fetching issue #{issue_id} from {url}")
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_related_merge_requests(self, issue_id: int) -> List[Dict[str, Any]]:
        url = f"{self.api_url}/projects/{self.project_id}/issues/{issue_id}/related_merge_requests"
        logger.info(f"Fetching related MRs for issue #{issue_id} from {url}")
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    def extract_issue_ids(self, description: str) -> List[int]:
        """Extract issue IDs from release description using regex."""
        pattern = r"#(\d+)"
        matches = re.findall(pattern, description or "")
        return [int(match) for match in matches]

    async def fetch_release_with_issues(self, tag_name: str) -> Release:
        release_data = await self.get_release(tag_name)
        issue_ids = self.extract_issue_ids(release_data.get("description", ""))
        issues = []
        for issue_id in issue_ids:
            try:
                issue_data = await self.get_issue(issue_id)
                # Fetch related merge requests
                mrs_data = await self.get_related_merge_requests(issue_id)
                merge_requests = []
                for mr_data in mrs_data:
                    mr = MergeRequest(
                        id=mr_data["id"],
                        title=mr_data["title"],
                        description=mr_data.get("description"),
                        state=mr_data["state"],
                        merged_at=mr_data.get("merged_at"),
                        target_branch=mr_data["target_branch"],
                        source_branch=mr_data["source_branch"],
                    )
                    merge_requests.append(mr)
                issue = Issue(
                    id=issue_data["id"],
                    title=issue_data["title"],
                    description=issue_data.get("description"),
                    state=issue_data["state"],
                    labels=issue_data.get("labels", []),
                    assignee=(
                        issue_data.get("assignee", {}).get("name")
                        if issue_data.get("assignee")
                        else None
                    ),
                    created_at=issue_data["created_at"],
                    updated_at=issue_data["updated_at"],
                    merge_requests=merge_requests,
                )
                issues.append(issue)
            except Exception as e:
                logger.error(f"Failed to fetch issue #{issue_id}: {e}")
        return Release(
            tag_name=release_data["tag_name"],
            name=release_data.get("name"),
            description=release_data.get("description"),
            created_at=release_data["created_at"],
            released_at=release_data.get("released_at"),
            issues=issues,
        )

    async def close(self) -> None:
        await self.client.aclose()
