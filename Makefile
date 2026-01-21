.PHONY: install test lint format clean build run

install:
	poetry install

test:
	poetry run pytest tests/ --cov=src --cov-report=term

lint:
	poetry run flake8 src/
	poetry run mypy src/

format:
	poetry run black src/

clean:
	rm -rf output/
	rm -rf .coverage
	rm -rf coverage.xml

build:
	docker build -t gitlab-reporter .

run:
	docker run --rm -e GITLAB_TOKEN=$(GITLAB_TOKEN) -e GITLAB_PROJECT_ID=$(GITLAB_PROJECT_ID) gitlab-reporter $(TAG)

dev:
	poetry run python src/main.py $(TAG) --dry-run