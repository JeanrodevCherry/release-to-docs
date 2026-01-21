import asyncio
import os
import yaml
from pathlib import Path
from loguru import logger
from prometheus_client import start_http_server, Counter
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from .models import Config
from .gitlab import GitLabClient
from .report import ReportGenerator

# Prometheus metrics
reports_generated = Counter(
    "reports_generated_total", "Total number of reports generated"
)
api_call_errors = Counter("api_call_errors_total", "Total number of API call errors")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()


def start_health_server(port: int) -> None:
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    logger.info(f"Health server started on port {port}")


def load_config(config_path: str) -> Config:
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    # Override with environment variables
    gitlab_token = os.getenv("GITLAB_TOKEN")
    if gitlab_token:
        config_data["gitlab"]["token"] = gitlab_token

    gitlab_project_id = os.getenv("GITLAB_PROJECT_ID")
    if gitlab_project_id:
        config_data["gitlab"]["project_id"] = int(gitlab_project_id)

    return Config(
        gitlab_api_url=config_data["gitlab"]["api_url"],
        gitlab_project_id=config_data["gitlab"]["project_id"],
        gitlab_token=config_data["gitlab"]["token"],
        gitlab_retries=config_data["gitlab"]["retries"],
        gitlab_timeout=config_data["gitlab"]["timeout"],
        report_output_dir=config_data["report"]["output_dir"],
        report_formats=config_data["report"]["formats"],
        report_templates=config_data["report"]["templates"],
        logging_level=config_data["logging"]["level"],
        logging_format=config_data["logging"]["format"],
        prometheus_port=config_data["prometheus"]["port"],
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description="Generate GitLab release reports")
    parser.add_argument("tag_name", help="Release tag name (e.g., v1.0.0)")
    parser.add_argument(
        "--config", default="config/config.yaml", help="Path to config file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config without generating reports",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    # Setup logging
    logger.remove()
    logger.add(
        lambda msg: print(msg), level=config.logging_level, format=config.logging_format
    )

    # Start Prometheus server
    start_http_server(config.prometheus_port)
    logger.info(f"Prometheus metrics server started on port {config.prometheus_port}")

    # Start health server on port 8080
    start_health_server(8080)

    if args.dry_run:
        logger.info("Dry run: Config validated successfully")
        return

    client = GitLabClient(
        api_url=config.gitlab_api_url,
        token=config.gitlab_token,
        project_id=config.gitlab_project_id,
        timeout=config.gitlab_timeout,
    )

    try:
        release = await client.fetch_release_with_issues(args.tag_name)
        logger.info(
            f"Fetched release {release.tag_name} with {len(release.issues)} issues"
        )

        generator = ReportGenerator(
            output_dir=config.report_output_dir,
            templates_dir=str(Path(config.report_templates["markdown"]).parent),
        )

        results = generator.generate_reports(release, config.report_formats)
        reports_generated.inc()
        logger.info(f"Reports generated: {results}")

    except Exception as e:
        api_call_errors.inc()
        logger.error(f"Error generating report: {e}")
        raise
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
