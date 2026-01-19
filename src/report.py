from typing import List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd
from loguru import logger
from .models import Release, Issue


class ReportGenerator:
    def __init__(self, output_dir: str, templates_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.templates_dir = Path(templates_dir)
        self.jinja_env = Environment(loader=FileSystemLoader(self.templates_dir))

    def group_issues_by_type(self, issues: List[Issue]) -> dict[str, List[Issue]]:
        grouped: dict[str, List[Issue]] = {"bug": [], "feature": [], "task": []}
        for issue in issues:
            issue_type = "task"  # default
            if any(label.lower() in ["bug", "fix"] for label in issue.labels):
                issue_type = "bug"
            elif any(
                label.lower() in ["feature", "enhancement"] for label in issue.labels
            ):
                issue_type = "feature"
            grouped[issue_type].append(issue)
        return grouped

    def generate_markdown(self, release: Release) -> str:
        template = self.jinja_env.get_template("report.md.j2")
        grouped_issues = self.group_issues_by_type(release.issues)
        return template.render(release=release, grouped_issues=grouped_issues)

    def generate_excel(self, release: Release) -> str:
        data = []
        for issue in release.issues:
            data.append(
                {
                    "ID": issue.id,
                    "Title": issue.title,
                    "State": issue.state,
                    "Labels": ", ".join(issue.labels),
                    "Assignee": issue.assignee or "Unassigned",
                    "Created At": issue.created_at,
                    "Updated At": issue.updated_at,
                }
            )
        df = pd.DataFrame(data)
        file_path = self.output_dir / f"release_{release.tag_name}.xlsx"
        df.to_excel(file_path, index=False)
        return str(file_path)

    def generate_pdf(self, release: Release) -> str:
        file_path = self.output_dir / f"release_{release.tag_name}.pdf"
        doc = SimpleDocTemplate(str(file_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph(f"Release Report: {release.tag_name}", styles["Title"]))
        story.append(Spacer(1, 12))

        # Summary
        story.append(
            Paragraph(
                f"Release Date: {release.released_at or release.created_at}",
                styles["Heading2"],
            )
        )
        story.append(
            Paragraph(f"Total Issues: {len(release.issues)}", styles["Normal"])
        )
        story.append(Spacer(1, 12))

        # Issues table
        data = [["ID", "Title", "State", "Assignee"]]
        for issue in release.issues:
            data.append(
                [
                    str(issue.id),
                    issue.title,
                    issue.state,
                    issue.assignee or "Unassigned",
                ]
            )
        table = Table(data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), (0.8, 0.8, 0.8)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), (0, 0, 0)),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BORDERS", (0, 0), (-1, -1), 1, (0, 0, 0)),
                    ("BACKGROUND", (0, 1), (-1, -1), (1, 1, 1)),
                ]
            )
        )
        story.append(table)

        doc.build(story)
        return str(file_path)

    def generate_reports(self, release: Release, formats: List[str]) -> dict:
        results = {}
        for fmt in formats:
            try:
                if fmt == "markdown":
                    content = self.generate_markdown(release)
                    file_path = self.output_dir / f"release_{release.tag_name}.md"
                    with open(file_path, "w") as f:
                        f.write(content)
                    results["markdown"] = str(file_path)
                elif fmt == "excel":
                    results["excel"] = self.generate_excel(release)
                elif fmt == "pdf":
                    results["pdf"] = self.generate_pdf(release)
                logger.info(f"Generated {fmt} report for {release.tag_name}")
            except Exception as e:
                logger.error(f"Failed to generate {fmt} report: {e}")
        return results
