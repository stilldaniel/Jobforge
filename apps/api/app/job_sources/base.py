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


class JobSource(ABC):

    @abstractmethod
    def fetch_jobs(self) -> list[DiscoveredJob]:
        """Fetch jobs from this source."""
        raise NotImplementedError