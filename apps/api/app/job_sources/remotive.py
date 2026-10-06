from app.job_sources.base import DiscoveredJob, JobSource
from app.job_sources.common import (
    MAX_SEARCH_QUERIES,
    clean_str,
    get_json,
    html_to_text,
    parse_iso_datetime,
)


class RemotiveJobSource(JobSource):
    """
    Remote jobs from Remotive (https://remotive.com/api-documentation).

    Terms: link back to the Remotive job URL and credit Remotive as the
    source. Remotive asks for at most 4 requests a day and does not allow
    its jobs to be shown in exchange for sign-ups without a paid API plan.
    """

    BASE_URL = "https://remotive.com/api/remote-jobs"

    filter_by_relevance = True
    # Remotive's terms: at most 4 requests a day. Its jobs are also
    # published with a 24-hour delay, so frequent polling gains nothing.
    min_interval_minutes = 360

    def __init__(self, limit: int = 50):
        self.limit = limit

    def fetch_jobs(self) -> list[DiscoveredJob]:
        queries = self.search_queries[:MAX_SEARCH_QUERIES] or [None]

        jobs: list[DiscoveredJob] = []

        for query in queries:
            params = {"limit": self.limit}

            if query:
                params["search"] = query

            data = get_json(self.BASE_URL, params=params)

            jobs.extend(
                self._map_job(item)
                for item in data.get("jobs", [])
                if item.get("url")
            )

        return jobs

    @staticmethod
    def _map_job(item: dict) -> DiscoveredJob:
        return DiscoveredJob(
            title=clean_str(item.get("title")) or "Untitled Job",
            company=clean_str(item.get("company_name")) or "Unknown Company",
            description=html_to_text(item.get("description")),
            location="Remote",
            remote_eligibility=clean_str(
                item.get("candidate_required_location")
            ),
            work_type="remote",
            # Remotive salaries are free text ("$20k -$35k"), so they
            # are not reliable enough to score against.
            salary_min=None,
            salary_max=None,
            application_url=item["url"],
            source="remotive",
            posted_at=parse_iso_datetime(item.get("publication_date")),
        )
