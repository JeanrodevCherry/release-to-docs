from typing import List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
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
            mr_titles = [mr.title for mr in issue.merge_requests]
            data.append(
                {
                    "ID": issue.id,
                    "Title": issue.title,
                    "State": issue.state,
                    "Labels": ", ".join(issue.labels),
                    "Assignee": issue.assignee or "Unassigned",
                    "Description": issue.description or "",
                    "Merge Requests": "; ".join(mr_titles),
                    "Created At": issue.created_at.replace(tzinfo=None),
                    "Updated At": issue.updated_at.replace(tzinfo=None),
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
        
        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center
        )
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        normal_style = styles['Normal']
        
        story = []

        # Title
        story.append(Paragraph(f"Release Report: {release.tag_name}", title_style))
        story.append(Spacer(1, 12))

        # Summary
        story.append(Paragraph(f"Release Date: {release.released_at or release.created_at}", heading_style))
        story.append(Paragraph(f"Total Issues: {len(release.issues)}", normal_style))
        story.append(Spacer(1, 12))

        # Release Description
        if release.description:
            story.append(Paragraph("Release Description", heading_style))
            story.append(Paragraph(release.description, normal_style))
            story.append(Spacer(1, 12))

        # Grouped Issues
        grouped_issues = self.group_issues_by_type(release.issues)

        for issue_type, issues in grouped_issues.items():
            if issues:
                story.append(Paragraph(f"{issue_type.capitalize()}s", heading_style))
                for issue in issues:
                    story.append(Paragraph(f"#{issue.id}: {issue.title} ({issue.state}) - Assignee: {issue.assignee or 'Unassigned'}", normal_style))
                    if issue.description:
                        story.append(Paragraph("Description:", heading_style))
                        story.append(Paragraph(issue.description, normal_style))
                    if issue.merge_requests:
                        story.append(Paragraph("Related Merge Requests:", heading_style))
                        for mr in issue.merge_requests:
                            story.append(Paragraph(f"!{mr.id}: {mr.title} ({mr.state}) - Merged: {mr.merged_at or 'Not merged'}", normal_style))
                            if mr.description:
                                story.append(Paragraph(mr.description, normal_style))
                    story.append(Spacer(1, 6))
                story.append(Spacer(1, 12))

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
