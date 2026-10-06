import re
import xml.etree.ElementTree as ElementTree

from app.job_sources.base import DiscoveredJob, JobSource
from app.job_sources.common import (
    clean_str,
    get_text,
    html_to_text,
    parse_rfc822,
)


class WeWorkRemotelyJobSource(JobSource):
    """
    Remote jobs from the We Work Remotely RSS feed.
    """

    FEED_URL = "https://weworkremotely.com/remote-jobs.rss"

    filter_by_relevance = True

    def fetch_jobs(self) -> list[DiscoveredJob]:
        root = ElementTree.fromstring(get_text(self.FEED_URL))

        jobs: list[DiscoveredJob] = []

        for item in root.iter("item"):
            job = self._map_item(item)

            if job:
                jobs.append(job)

        return jobs

    @staticmethod
    def _map_item(item: ElementTree.Element) -> DiscoveredJob | None:
        def text(tag: str) -> str | None:
            return clean_str(item.findtext(tag))

        link = text("link") or text("guid")
        raw_title = text("title")

        if not link or not raw_title:
            return None

        # Titles are formatted as "Company: Job title".
        company, separator, title = raw_title.partition(": ")

        if not separator:
            company, title = "Unknown Company", raw_title

        region = text("region")
        country = text("country")

        # Countries are prefixed with a flag emoji ("🇲🇽 Mexico").
        if country:
            country = re.sub(r"^[^\w]+", "", country).strip() or None

        return DiscoveredJob(
            title=title.strip() or "Untitled Job",
            company=company.strip() or "Unknown Company",
            description=html_to_text(item.findtext("description")),
            location="Remote",
            remote_eligibility=region or country,
            work_type="remote",
            salary_min=None,
            salary_max=None,
            application_url=link,
            source="weworkremotely",
            posted_at=parse_rfc822(text("pubDate")),
        )
