from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DiscoveredJob:
    title: str
    company: str
    description: str | None
    location: str | None
    work_type: str | None
    salary_min: int | None
    salary_max: int | None
    application_url: str
    source: str
    posted_at: datetime | None
    remote_eligibility: str | None = None
    salary_currency: str | None = None
    salary_period: str | None = None


class JobSource(ABC):
    # Search terms derived from users' career profiles. The monitor
    # sets these before each fetch; sources with a search API use them.
    search_queries: list[str] = []

    # Broad feeds return every job they have, so the monitor keeps
    # only the jobs relevant to at least one career profile.
    filter_by_relevance: bool = False

    # Minimum time between fetches. Some platforms ask API users
    # not to poll them more often than this.
    min_interval_minutes: int = 0

    @abstractmethod
    def fetch_jobs(self) -> list[DiscoveredJob]:
        """Fetch jobs from this source."""
        raise NotImplementedError
