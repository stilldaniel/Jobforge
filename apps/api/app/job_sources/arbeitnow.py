from app.job_sources.base import DiscoveredJob, JobSource
from app.job_sources.common import (
    clean_str,
    get_json,
    html_to_text,
    parse_epoch,
)


class ArbeitnowJobSource(JobSource):
    """
    Jobs from Arbeitnow (https://www.arbeitnow.com/blog/job-board-api).

    Mostly Europe-based roles, many of them remote. Terms: do not abuse
    the API and link back to Arbeitnow.
    """

    BASE_URL = "https://www.arbeitnow.com/api/job-board-api"

    filter_by_relevance = True
    # Arbeitnow refreshes its feed hourly, so fetching more often
    # finds nothing new.
    min_interval_minutes = 60

    def fetch_jobs(self) -> list[DiscoveredJob]:
        # The feed is sorted newest first and the first page holds a few
        # hundred jobs, which covers everything posted between fetches.
        data = get_json(self.BASE_URL, params={"page": 1})

        return [
            self._map_job(item)
            for item in data.get("data", [])
            if item.get("url")
        ]

    @staticmethod
    def _map_job(item: dict) -> DiscoveredJob:
        is_remote = bool(item.get("remote"))

        return DiscoveredJob(
            title=clean_str(item.get("title")) or "Untitled Job",
            company=clean_str(item.get("company_name")) or "Unknown Company",
            description=html_to_text(item.get("description")),
            location=clean_str(item.get("location")),
            remote_eligibility=None,
            work_type="remote" if is_remote else None,
            salary_min=None,
            salary_max=None,
            application_url=item["url"],
            source="arbeitnow",
            posted_at=parse_epoch(item.get("created_at")),
        )
