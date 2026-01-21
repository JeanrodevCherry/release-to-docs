# GitLab Release Reporter

[![CI](https://github.com/jpeiteado/release-to-docs/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/JeanrodevCherry/release-to-docs/actions)
[![codecov](https://codecov.io/gh/jpeiteado/release-to-docs/branch/main/graph/badge.svg)](https://codecov.io/gh/jpeiteado/release-to-docs)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com)

A Dockerized Python application that fetches GitLab release data, extracts linked issues, and generates structured reports in PDF, Excel, and Markdown formats.

## Features

- **GitLab API Integration**: Fetches release details and associated issues
- **Multiple Report Formats**: Generate PDF, Excel, and Markdown reports
- **Issue Grouping**: Automatically groups issues by type (bug/feature/task)
- **Configurable**: Use YAML config files and environment variables
- **Production-Ready**: Includes unit tests, linting, Docker, and CI/CD

## Installation
<!-- 
### Using Docker

```bash
docker build -t gitlab-reporter .
docker run -e GITLAB_TOKEN=your_token -e GITLAB_PROJECT_ID=123 gitlab-reporter v1.0.0
``` -->

### Using Docker Compose

```bash
docker-compose up --build
```

### Local Development

```bash
pip install poetry
poetry install
poetry run python src/main.py v1.0.0
## Environment Setup

Create a `.env` file in the root directory with the following variables:

```env
GITLAB_TOKEN="your_gitlab_token_here"
GITLAB_PROJECT_ID=your_project_id_here
GITLAB_RELEASE_TAG="your_release_tag_here"
```

Replace the placeholders with your actual GitLab token, project ID, and release tag.

## Configuration

Edit `config/config.yaml`:

```yaml
gitlab:
  api_url: "https://gitlab.com/api/v4"
  project_id: 123456
  token: "${GITLAB_TOKEN}"
  retries: 3
  timeout: 30.0

report:
  output_dir: "output"
  formats: ["pdf", "excel", "markdown"]
```

Override with environment variables:
- `GITLAB_TOKEN`
- `GITLAB_PROJECT_ID`

## Usage

```bash
python src/main.py <tag_name> [--config config/config.yaml] [--dry-run]
```

## Testing

```bash
poetry run pytest tests/ --cov=src
```

## Linting and Formatting

```bash
poetry run black src/
poetry run flake8 src/
poetry run mypy src/
```

## Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

## CI/CD

The project includes GitHub Actions CI/CD pipeline for testing, building, and deploying Docker images.

### Workflows

- **Test**: Runs on every push and pull request to `main` and `develop` branches
  - Unit tests with coverage reporting
  - Code linting with flake8
  - Type checking with mypy
  - Coverage upload to Codecov

- **Build & Push**: Runs on pushes to `main` branch and releases
  - Builds Docker image
  - Pushes to Docker Hub with appropriate tags

- **Deploy**: Runs on published releases
  - Deploys to production environment

- **Auto-merge**: Runs on Dependabot pull requests
  - Automatically approves and merges patch/minor dependency updates
  - Only affects PRs with `dependencies` and `automated` labels

### Required Secrets

For Docker Hub publishing, add these secrets to your GitHub repository:
- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub password or access token

### Dependabot Auto-merge

The repository is configured to automatically merge Dependabot pull requests for:
- **Patch updates** (e.g., `1.2.3` → `1.2.4`)
- **Minor updates** (e.g., `1.2.3` → `1.3.0`)

**Major updates** require manual review and approval.

This ensures dependencies stay up-to-date while maintaining stability by avoiding breaking changes from major version updates.

## Project Structure

```
./
├── Dockerfile
├── docker-compose.yml
├── .pre-commit-config.yaml
├── pyproject.toml
├── config/
│   └── config.yaml
├── src/
│   ├── main.py
│   ├── gitlab.py
│   ├── report.py
│   ├── models.py
│   └── templates/
├── tests/
│   ├── test_gitlab.py
│   └── test_report.py
└── .gitlab-ci.yml
```
