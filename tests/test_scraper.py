import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.scraper import JobPosting, parse_job_postings  # noqa: E402


def test_parse_job_postings() -> None:
    """Verify job postings parsing from sample HTML."""
    sample_file = Path(__file__).parent / "data" / "sample_jobs.html"
    html = sample_file.read_text(encoding="utf-8")
    results = parse_job_postings(html)
    assert len(results) == 2
    assert results[0] == JobPosting(
        title="Software Engineer",
        link="https://www.linkedin.com/jobs/view/12345",
    )
    assert results[1] == JobPosting(
        title="Data Scientist",
        link="https://www.linkedin.com/jobs/view/67890",
    )
