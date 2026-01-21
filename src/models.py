from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Commit(BaseModel):
    id: str
    title: str
    message: str
    author_name: str
    created_at: datetime


class Issue(BaseModel):
    id: int
    title: str
    description: Optional[str]
    state: str
    labels: List[str]
    assignee: Optional[str]
    created_at: datetime
    updated_at: datetime
    commits: List[Commit] = []


class Release(BaseModel):
    tag_name: str
    name: Optional[str]
    description: Optional[str]
    created_at: datetime
    released_at: Optional[datetime]
    issues: List[Issue]


class Config(BaseModel):
    gitlab_api_url: str
    gitlab_project_id: int
    gitlab_token: str
    gitlab_retries: int
    gitlab_timeout: float
    report_output_dir: str
    report_formats: List[str]
    report_templates: dict
    logging_level: str
    logging_format: str
    prometheus_port: int
