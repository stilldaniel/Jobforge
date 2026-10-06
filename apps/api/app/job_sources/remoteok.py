from app.job_sources.base import DiscoveredJob, JobSource
from app.job_sources.common import (
    clean_str,
    get_json,
    html_to_text,
    normalize_salary,
    parse_iso_datetime,
)


class RemoteOKJobSource(JobSource):
    """
    Remote jobs from Remote OK (https://remoteok.com/api).

    Terms: link back to the Remote OK job URL (without rel="nofollow")
    and mention Remote OK as the source. Do not use the Remote OK logo.
    """

    BASE_URL = "https://remoteok.com/api"

    filter_by_relevance = True

    def fetch_jobs(self) -> list[DiscoveredJob]:
        data = get_json(self.BASE_URL)

        # The first element is a legal notice, not a job.
        return [
            self._map_job(item)
            for item in data
            if isinstance(item, dict)
            and item.get("position")
            and item.get("url")
        ]

    @staticmethod
    def _map_job(item: dict) -> DiscoveredJob:
        salary_min, salary_max, currency, period = normalize_salary(
            item.get("salary_min"),
            item.get("salary_max"),
            "USD",
            "year",
        )

        return DiscoveredJob(
            title=clean_str(item.get("position")) or "Untitled Job",
            company=clean_str(item.get("company")) or "Unknown Company",
            description=html_to_text(item.get("description")),
            location="Remote",
            remote_eligibility=clean_str(item.get("location")),
            work_type="remote",
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=currency,
            salary_period=period,
            application_url=item["url"],
            source="remoteok",
            posted_at=parse_iso_datetime(item.get("date")),
        )
