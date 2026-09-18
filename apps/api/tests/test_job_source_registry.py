import pytest

from app.job_sources.adzuna import AdzunaJobSource
from app.job_sources.base import DiscoveredJob, JobSource
from app.job_sources.mock import MockJobSource
from app.job_sources.registry import get_job_sources


class FakeJobSource(JobSource):
    def __init__(self, company: str):
        self.company = company

    def fetch_jobs(self) -> list[DiscoveredJob]:
        return [
            DiscoveredJob(
                title="Frontend Developer",
                company=self.company,
                description="Test job",
                location="Lagos, Nigeria",
                work_type="remote",
                salary_min=2000,
                salary_max=4000,
                application_url="https://example.com",
                source="test",
                posted_at=None,
                remote_eligibility="Remote",
            )
        ]


class FailingJobSource(JobSource):
    def fetch_jobs(self) -> list[DiscoveredJob]:
        raise RuntimeError("API timeout")


def test_default_registry_returns_mock_source(monkeypatch):
    monkeypatch.delenv("JOB_SOURCES", raising=False)

    sources = get_job_sources()

    assert len(sources) == 1
    assert isinstance(sources[0], MockJobSource)


def test_registry_returns_configured_mock_source(monkeypatch):
    monkeypatch.setenv("JOB_SOURCES", "mock")

    sources = get_job_sources()

    assert len(sources) == 1
    assert isinstance(sources[0], MockJobSource)


def test_registry_returns_configured_adzuna_source(monkeypatch):
    monkeypatch.setenv("JOB_SOURCES", "adzuna")
    monkeypatch.setenv("ADZUNA_APP_ID", "test-app-id")
    monkeypatch.setenv("ADZUNA_APP_KEY", "test-app-key")

    sources = get_job_sources()

    assert len(sources) == 1
    assert isinstance(sources[0], AdzunaJobSource)


def test_registry_supports_multiple_sources(monkeypatch):
    monkeypatch.setenv("JOB_SOURCES", "mock,adzuna")
    monkeypatch.setenv("ADZUNA_APP_ID", "test-app-id")
    monkeypatch.setenv("ADZUNA_APP_KEY", "test-app-key")

    sources = get_job_sources()

    assert len(sources) == 2
    assert isinstance(sources[0], MockJobSource)
    assert isinstance(sources[1], AdzunaJobSource)


def test_registry_ignores_whitespace_and_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("JOB_SOURCES", " MOCK , ADZUNA ")
    monkeypatch.setenv("ADZUNA_APP_ID", "test-app-id")
    monkeypatch.setenv("ADZUNA_APP_KEY", "test-app-key")

    sources = get_job_sources()

    assert len(sources) == 2
    assert isinstance(sources[0], MockJobSource)
    assert isinstance(sources[1], AdzunaJobSource)


def test_registry_rejects_unknown_source(monkeypatch):
    monkeypatch.setenv("JOB_SOURCES", "unknown")

    with pytest.raises(ValueError, match="Unknown job source: unknown"):
        get_job_sources()