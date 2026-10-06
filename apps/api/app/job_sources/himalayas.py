from app.job_sources.base import DiscoveredJob, JobSource
from app.job_sources.common import (
    MAX_SEARCH_QUERIES,
    clean_str,
    get_json,
    html_to_text,
    normalize_salary,
    parse_epoch,
)


class HimalayasJobSource(JobSource):
    """
    Remote jobs from Himalayas (https://himalayas.app/api).

    Himalayas lists the countries each job accepts, which feeds the
    location eligibility check in the matching engine.
    """

    FEED_URL = "https://himalayas.app/jobs/api"
    SEARCH_URL = "https://himalayas.app/jobs/api/search"

    filter_by_relevance = True
    min_interval_minutes = 60

    def __init__(self, limit: int = 20):
        self.limit = limit

    def fetch_jobs(self) -> list[DiscoveredJob]:
        jobs: list[DiscoveredJob] = []

        queries = self.search_queries[:MAX_SEARCH_QUERIES]

        if not queries:
            data = get_json(self.FEED_URL, params={"limit": self.limit})
            return self._map_jobs(data)

        for query in queries:
            data = get_json(
                self.SEARCH_URL,
                params={"q": query, "limit": self.limit},
            )
            jobs.extend(self._map_jobs(data))

        return jobs

    def _map_jobs(self, data: dict) -> list[DiscoveredJob]:
        return [
            self._map_job(item)
            for item in data.get("jobs", [])
            if item.get("applicationLink") or item.get("guid")
        ]

    @staticmethod
    def _map_job(item: dict) -> DiscoveredJob:
        restrictions = [
            country
            for country in item.get("locationRestrictions") or []
            if isinstance(country, str) and country.strip()
        ]

        salary_min, salary_max, currency, period = normalize_salary(
            item.get("minSalary"),
            item.get("maxSalary"),
            item.get("currency"),
            item.get("salaryPeriod"),
        )

        return DiscoveredJob(
            title=clean_str(item.get("title")) or "Untitled Job",
            company=clean_str(item.get("companyName")) or "Unknown Company",
            description=html_to_text(
                item.get("description") or item.get("excerpt")
            ),
            location="Remote",
            # No restrictions means the job is open to any country.
            remote_eligibility=(
                ", ".join(restrictions) if restrictions else "Worldwide"
            ),
            work_type="remote",
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=currency,
            salary_period=period,
            application_url=item.get("applicationLink") or item["guid"],
            source="himalayas",
            posted_at=parse_epoch(item.get("pubDate")),
        )
