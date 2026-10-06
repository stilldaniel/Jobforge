"""
Jobs posted directly on company career pages hosted by applicant
tracking systems (Greenhouse, Lever, Ashby).

These APIs have no search, so each source reads the boards listed in
an environment variable, for example:

    GREENHOUSE_BOARDS=stripe,airbnb
    LEVER_COMPANIES=spotify,palantir
    ASHBY_BOARDS=ramp,linear
"""

import logging
import os
from abc import abstractmethod

from app.job_sources.base import DiscoveredJob, JobSource
from app.job_sources.common import (
    clean_str,
    company_from_slug,
    config_list,
    get_json,
    html_to_text,
    normalize_salary,
    parse_epoch,
    parse_iso_datetime,
)


logger = logging.getLogger(__name__)


class CompanyBoardJobSource(JobSource):
    """
    Fetches every configured company board. A single bad board (renamed
    or removed company) is logged and skipped; the source only fails
    when every board fails.
    """

    ENV_VAR: str

    filter_by_relevance = True

    def __init__(self, boards: list[str] | None = None):
        self.boards = (
            boards
            if boards is not None
            else config_list(os.getenv(self.ENV_VAR))
        )

    def fetch_jobs(self) -> list[DiscoveredJob]:
        jobs: list[DiscoveredJob] = []
        errors: list[str] = []

        for board in self.boards:
            try:
                jobs.extend(self.fetch_board(board))
            except Exception as exc:
                logger.warning(
                    "%s board failed: %s (%s)",
                    self.__class__.__name__,
                    board,
                    exc,
                )
                errors.append(f"{board}: {exc}")

        if self.boards and len(errors) == len(self.boards):
            raise RuntimeError(
                "All boards failed: " + "; ".join(errors)
            )

        return jobs

    @abstractmethod
    def fetch_board(self, board: str) -> list[DiscoveredJob]:
        raise NotImplementedError


def _remote_fields(
    location: str | None,
    is_remote: bool,
) -> tuple[str | None, str | None]:
    """
    Return (work_type, remote_eligibility) for a career-page job.

    For remote roles the location usually states the allowed region,
    e.g. "Remote - US" or "Remote (Europe)".
    """

    if not is_remote:
        return None, None

    return "remote", location


class GreenhouseJobSource(CompanyBoardJobSource):
    ENV_VAR = "GREENHOUSE_BOARDS"

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def fetch_board(self, board: str) -> list[DiscoveredJob]:
        data = get_json(
            f"{self.BASE_URL}/{board}/jobs",
            params={"content": "true"},
        )

        jobs: list[DiscoveredJob] = []

        for item in data.get("jobs", []):
            url = item.get("absolute_url")

            if not url:
                continue

            location = clean_str((item.get("location") or {}).get("name"))
            is_remote = "remote" in (location or "").lower()
            work_type, remote_eligibility = _remote_fields(
                location,
                is_remote,
            )

            jobs.append(
                DiscoveredJob(
                    title=clean_str(item.get("title")) or "Untitled Job",
                    company=(
                        clean_str(item.get("company_name"))
                        or company_from_slug(board)
                    ),
                    description=html_to_text(item.get("content")),
                    location=location,
                    remote_eligibility=remote_eligibility,
                    work_type=work_type,
                    salary_min=None,
                    salary_max=None,
                    application_url=url,
                    source="greenhouse",
                    posted_at=parse_iso_datetime(
                        item.get("first_published") or item.get("updated_at")
                    ),
                )
            )

        return jobs


LEVER_WORKPLACE_TYPES = {
    "remote": "remote",
    "hybrid": "hybrid",
    "onsite": "on-site",
    "on-site": "on-site",
}


class LeverJobSource(CompanyBoardJobSource):
    ENV_VAR = "LEVER_COMPANIES"

    BASE_URL = "https://api.lever.co/v0/postings"

    def fetch_board(self, board: str) -> list[DiscoveredJob]:
        data = get_json(
            f"{self.BASE_URL}/{board}",
            params={"mode": "json"},
        )

        jobs: list[DiscoveredJob] = []

        for item in data:
            url = item.get("hostedUrl") or item.get("applyUrl")

            if not url:
                continue

            categories = item.get("categories") or {}
            location = clean_str(categories.get("location"))
            work_type = LEVER_WORKPLACE_TYPES.get(
                (item.get("workplaceType") or "").lower()
            )

            salary = item.get("salaryRange") or {}
            salary_min, salary_max, currency, period = normalize_salary(
                salary.get("min"),
                salary.get("max"),
                salary.get("currency"),
                salary.get("interval"),
            )

            jobs.append(
                DiscoveredJob(
                    title=clean_str(item.get("text")) or "Untitled Job",
                    company=company_from_slug(board),
                    description=self._description(item),
                    location=location,
                    remote_eligibility=(
                        location if work_type == "remote" else None
                    ),
                    work_type=work_type,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency=currency,
                    salary_period=period,
                    application_url=url,
                    source="lever",
                    posted_at=parse_epoch(
                        item.get("createdAt"),
                        milliseconds=True,
                    ),
                )
            )

        return jobs

    @staticmethod
    def _description(item: dict) -> str | None:
        parts = [clean_str(item.get("descriptionPlain"))]

        for section in item.get("lists") or []:
            parts.append(clean_str(section.get("text")))
            parts.append(html_to_text(section.get("content")))

        parts.append(clean_str(item.get("additionalPlain")))

        text = "\n".join(part for part in parts if part)

        return text or None


ASHBY_WORKPLACE_TYPES = {
    "remote": "remote",
    "hybrid": "hybrid",
    "onsite": "on-site",
}


class AshbyJobSource(CompanyBoardJobSource):
    ENV_VAR = "ASHBY_BOARDS"

    BASE_URL = "https://api.ashbyhq.com/posting-api/job-board"

    def fetch_board(self, board: str) -> list[DiscoveredJob]:
        data = get_json(
            f"{self.BASE_URL}/{board}",
            params={"includeCompensation": "true"},
        )

        jobs: list[DiscoveredJob] = []

        for item in data.get("jobs", []):
            url = item.get("jobUrl") or item.get("applyUrl")

            if not url or item.get("isListed") is False:
                continue

            location = clean_str(item.get("location"))
            work_type = ASHBY_WORKPLACE_TYPES.get(
                (item.get("workplaceType") or "").lower()
            )

            if item.get("isRemote") and work_type is None:
                work_type = "remote"

            remote_eligibility = None

            if work_type == "remote":
                remote_locations = [
                    clean_str(entry.get("location"))
                    for entry in [item, *(item.get("secondaryLocations") or [])]
                    if "remote" in (entry.get("location") or "").lower()
                ]
                remote_eligibility = (
                    ", ".join(loc for loc in remote_locations if loc)
                    or location
                )

            salary_min, salary_max, currency, period = self._salary(item)

            jobs.append(
                DiscoveredJob(
                    title=clean_str(item.get("title")) or "Untitled Job",
                    company=company_from_slug(board),
                    description=(
                        clean_str(item.get("descriptionPlain"))
                        or html_to_text(item.get("descriptionHtml"))
                    ),
                    location=location,
                    remote_eligibility=remote_eligibility,
                    work_type=work_type,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency=currency,
                    salary_period=period,
                    application_url=url,
                    source="ashby",
                    posted_at=parse_iso_datetime(item.get("publishedAt")),
                )
            )

        return jobs

    @staticmethod
    def _salary(
        item: dict,
    ) -> tuple[int | None, int | None, str | None, str | None]:
        compensation = item.get("compensation") or {}

        for tier in compensation.get("compensationTiers") or []:
            for component in tier.get("components") or []:
                if component.get("compensationType") != "Salary":
                    continue

                result = normalize_salary(
                    component.get("minValue"),
                    component.get("maxValue"),
                    component.get("currencyCode"),
                    component.get("interval"),
                )

                if result[0] is not None or result[1] is not None:
                    return result

        return None, None, None, None
