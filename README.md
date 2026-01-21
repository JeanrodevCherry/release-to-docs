# GitLab Release Reporter

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

The project includes GitLab CI/CD pipeline for testing, building, and deploying Docker images.

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
