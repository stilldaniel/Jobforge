from unittest.mock import Mock, patch

import pytest

from app.job_sources.adzuna import AdzunaJobSource


def test_adzuna_source_requires_credentials():
    with patch.dict(
        "os.environ",
        {},
        clear=True,
    ):
        with pytest.raises(
            ValueError,
            match="ADZUNA_APP_ID",
        ):
            AdzunaJobSource()


def test_adzuna_source_maps_api_response():
    source = AdzunaJobSource(
        app_id="test-id",
        app_key="test-key",
        country="gb",
        query="frontend developer",
    )

    mock_response = Mock()

    mock_response.json.return_value = {
        "results": [
            {
                "title": "Senior Frontend Developer",
                "company": {
                    "display_name": "Test Company"
                },
                "description": (
                    "Remote frontend developer "
                    "working with React."
                ),
                "location": {
                    "display_name": "London"
                },
                "salary_min": 50000,
                "salary_max": 70000,
                "redirect_url": (
                    "https://example.com/job/123"
                ),
                "created": (
                    "2026-09-17T10:00:00Z"
                ),
            }
        ]
    }

    with patch(
        "app.job_sources.adzuna.httpx.get",
        return_value=mock_response,
    ) as mock_get:
        jobs = source.fetch_jobs()

    mock_get.assert_called_once()

    assert len(jobs) == 1

    job = jobs[0]

    assert job.title == "Senior Frontend Developer"
    assert job.company == "Test Company"
    assert job.location == "London"
    assert job.salary_min == 50000
    assert job.salary_max == 70000
    assert job.application_url == (
        "https://example.com/job/123"
    )
    assert job.source == "adzuna"
    assert job.remote_eligibility == "Remote"


def test_adzuna_source_handles_missing_salary():
    source = AdzunaJobSource(
        app_id="test-id",
        app_key="test-key",
        country="gb",
    )

    mock_response = Mock()

    mock_response.json.return_value = {
        "results": [
            {
                "title": "Frontend Developer",
                "company": {
                    "display_name": "Test Company"
                },
                "description": "Frontend development.",
                "location": {
                    "display_name": "London"
                },
                "redirect_url": (
                    "https://example.com/job/456"
                ),
            }
        ]
    }

    with patch(
        "app.job_sources.adzuna.httpx.get",
        return_value=mock_response,
    ):
        jobs = source.fetch_jobs()

    assert len(jobs) == 1
    assert jobs[0].salary_min is None
    assert jobs[0].salary_max is None