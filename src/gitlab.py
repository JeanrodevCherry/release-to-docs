import httpx
import re
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Dict, Any
from loguru import logger
from .models import Issue, Release, MergeRequest, Commit, FileChange


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

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_releases(self) -> List[Dict[str, Any]]:
        url = f"{self.api_url}/projects/{self.project_id}/releases"
        logger.info(f"Fetching all releases from {url}")
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_commits_for_tag(self, tag_name: str) -> List[Dict[str, Any]]:
        # Fallback method to get commits for a tag when no previous release exists
        url = f"{self.api_url}/projects/{self.project_id}/repository/commits"
        params = {"ref_name": tag_name, "per_page": 100}  # Limit to 100 commits for now
        logger.info(f"Fetching commits for tag {tag_name} from {url}")
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def compare_releases(self, from_ref: str, to_ref: str) -> Dict[str, Any]:
        url = f"{self.api_url}/projects/{self.project_id}/repository/compare"
        params = {"from": from_ref, "to": to_ref}
        logger.info(f"Comparing {from_ref} to {to_ref} from {url}")
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_commit_diff(self, commit_sha: str) -> List[Dict[str, Any]]:
        url = f"{self.api_url}/projects/{self.project_id}/repository/commits/{commit_sha}/diff"
        logger.info(f"Fetching diff for commit {commit_sha} from {url}")
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

        # Fetch commits and diffs for the release (comparing with previous release)
        commits = []
        try:
            # Get all releases to find the previous one
            all_releases = await self.get_releases()
            releases_sorted = sorted(all_releases, key=lambda r: r["created_at"], reverse=True)
            
            # Find current release and previous release
            current_release = None
            previous_release = None
            
            for release in releases_sorted:
                if release["tag_name"] == tag_name:
                    current_release = release
                    break
            
            if current_release:
                # Find the previous release (next one in the sorted list)
                current_index = releases_sorted.index(current_release)
                if current_index + 1 < len(releases_sorted):
                    previous_release = releases_sorted[current_index + 1]
            
            if previous_release:
                # Compare current release with previous release
                compare_data = await self.compare_releases(previous_release["tag_name"], tag_name)
                commits_data = compare_data.get("commits", [])
            else:
                # If no previous release, get commits for current tag
                commits_data = await self.get_commits_for_tag(tag_name)
            
            for commit_data in commits_data[:20]:  # Limit to first 20 commits for brevity
                try:
                    diff_data = await self.get_commit_diff(commit_data["id"])
                    file_changes = []
                    for diff in diff_data:
                        # Only include text-based files
                        file_path = diff["new_path"]
                        if any(file_path.endswith(ext) for ext in ['.py', '.md', '.txt', '.cpp', '.c', '.h', '.java', '.js', '.ts', '.html', '.css', '.yml', '.yaml', '.json', '.xml', '.sh', '.bash']):
                            file_change = FileChange(
                                file_path=file_path,
                                additions=diff.get("additions", 0),
                                deletions=diff.get("deletions", 0),
                                diff=diff.get("diff", "")
                            )
                            file_changes.append(file_change)
                    
                    commit = Commit(
                        id=commit_data["id"],
                        title=commit_data["title"],
                        message=commit_data["message"],
                        author_name=commit_data["author_name"],
                        created_at=commit_data["created_at"],
                        file_changes=file_changes
                    )
                    commits.append(commit)
                except Exception as e:
                    logger.error(f"Failed to fetch diff for commit {commit_data['id']}: {e}")
        except Exception as e:
            logger.error(f"Failed to fetch commits for tag {tag_name}: {e}")

        return Release(
            tag_name=release_data["tag_name"],
            name=release_data.get("name"),
            description=release_data.get("description"),
            created_at=release_data["created_at"],
            released_at=release_data.get("released_at"),
            issues=issues,
            commits=commits,
        )

    async def close(self) -> None:
        await self.client.aclose()
