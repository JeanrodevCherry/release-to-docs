import pytest
from pathlib import Path
from src.report import ReportGenerator
from src.models import Release, Issue
from datetime import datetime

@pytest.fixture
def sample_release():
    issues = [
        Issue(
            id=123,
            title="Fix critical bug",
            description="Bug fix",
            state="closed",
            labels=["bug"],
            assignee="John Doe",
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 1, 2)
        ),
        Issue(
            id=456,
            title="Add new feature",
            description="Feature",
            state="closed",
            labels=["feature"],
            assignee="Jane Smith",
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 1, 2)
        )
    ]
    return Release(
        tag_name="v1.0.0",
        name="Version 1.0.0",
        description="Release description",
        created_at=datetime(2023, 1, 1),
        released_at=datetime(2023, 1, 1),
        issues=issues
    )

@pytest.fixture
def report_generator(tmp_path):
    templates_dir = Path(__file__).parent.parent / "src" / "templates"
    return ReportGenerator(output_dir=str(tmp_path), templates_dir=str(templates_dir))

def test_group_issues_by_type(report_generator, sample_release):
    grouped = report_generator.group_issues_by_type(sample_release.issues)
    assert len(grouped['bug']) == 1
    assert len(grouped['feature']) == 1
    assert len(grouped['task']) == 0

def test_generate_markdown(report_generator, sample_release):
    md_content = report_generator.generate_markdown(sample_release)
    assert "Release Report: v1.0.0" in md_content
    assert "Fix critical bug" in md_content
    assert "Add new feature" in md_content

def test_generate_excel(report_generator, sample_release):
    file_path = report_generator.generate_excel(sample_release)
    assert Path(file_path).exists()
    assert file_path.endswith(".xlsx")

def test_generate_pdf(report_generator, sample_release):
    file_path = report_generator.generate_pdf(sample_release)
    assert Path(file_path).exists()
    assert file_path.endswith(".pdf")

def test_generate_reports(report_generator, sample_release):
    results = report_generator.generate_reports(sample_release, ["markdown", "excel", "pdf"])
    assert "markdown" in results
    assert "excel" in results
    assert "pdf" in results
    for path in results.values():
        assert Path(path).exists()