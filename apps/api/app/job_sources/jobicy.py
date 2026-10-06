from app.job_sources.base import DiscoveredJob, JobSource
from app.job_sources.common import (
    clean_str,
    get_json,
    html_to_text,
    normalize_salary,
    parse_iso_datetime,
)


class JobicyJobSource(JobSource):
    """
    Remote jobs from Jobicy (https://jobi.cy/apidocs).

    Terms: credit Jobicy with a direct link to the source, and send
    applicants to the original job URL from the feed.
    """

    BASE_URL = "https://jobicy.com/api/v2/remote-jobs"

    filter_by_relevance = True
    min_interval_minutes = 60

    def __init__(self, count: int = 100):
        self.count = count

    def fetch_jobs(self) -> list[DiscoveredJob]:
        data = get_json(self.BASE_URL, params={"count": self.count})

        return [
            self._map_job(item)
            for item in data.get("jobs", [])
            if item.get("url")
        ]

    @staticmethod
    def _map_job(item: dict) -> DiscoveredJob:
        salary_min, salary_max, currency, period = normalize_salary(
            item.get("salaryMin") or item.get("annualSalaryMin"),
            item.get("salaryMax") or item.get("annualSalaryMax"),
            item.get("salaryCurrency"),
            item.get("salaryPeriod")
            or ("year" if item.get("annualSalaryMin") else None),
        )

        return DiscoveredJob(
            title=clean_str(item.get("jobTitle")) or "Untitled Job",
            company=clean_str(item.get("companyName")) or "Unknown Company",
            description=html_to_text(
                item.get("jobDescription") or item.get("jobExcerpt")
            ),
            location="Remote",
            remote_eligibility=clean_str(item.get("jobGeo")),
            work_type="remote",
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=currency,
            salary_period=period,
            application_url=item["url"],
            source="jobicy",
            posted_at=parse_iso_datetime(item.get("pubDate")),
        )
