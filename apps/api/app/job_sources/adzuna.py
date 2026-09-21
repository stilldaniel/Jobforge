import os
from datetime import datetime

import httpx

from app.job_sources.base import DiscoveredJob, JobSource


class AdzunaJobSource(JobSource):
    """
    Job source implementation for the Adzuna Jobs API.
    """

    BASE_URL = "https://api.adzuna.com/v1/api"

    def __init__(
        self,
        app_id: str | None = None,
        app_key: str | None = None,
        country: str | None = None,
        query: str = "frontend developer",
        location: str | None = None,
        results_per_page: int = 20,
        timeout: float = 30.0,
    ):
        self.app_id = app_id or os.getenv("ADZUNA_APP_ID")
        self.app_key = app_key or os.getenv("ADZUNA_APP_KEY")
        self.country = country or os.getenv(
            "ADZUNA_COUNTRY",
            "gb",
        )
        self.query = query
        self.location = location
        self.results_per_page = results_per_page
        self.timeout = timeout

        if not self.app_id:
            raise ValueError(
                "ADZUNA_APP_ID is not configured"
            )

        if not self.app_key:
            raise ValueError(
                "ADZUNA_APP_KEY is not configured"
            )

    def fetch_jobs(self) -> list[DiscoveredJob]:
        url = (
            f"{self.BASE_URL}/jobs/"
            f"{self.country}/search/1"
        )

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": self.results_per_page,
            "what": self.query,
        }

        if self.location:
            params["where"] = self.location

        response = httpx.get(
            url,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        discovered_jobs: list[DiscoveredJob] = []

        for item in data.get("results", []):
            location_data = item.get("location") or {}

            location_name = location_data.get(
                "display_name"
            )

            company_data = item.get("company") or {}

            posted_at = self._parse_datetime(
                item.get("created")
            )

            discovered_jobs.append(
                DiscoveredJob(
                    title=item.get(
                        "title",
                        "Untitled Job",
                    ),
                    company=company_data.get(
                        "display_name",
                        "Unknown Company",
                    ),
                    description=item.get(
                        "description"
                    ),
                    location=location_name,
                    work_type=self._extract_work_type(
                        item
                    ),
                    salary_min=self._to_int(
                        item.get("salary_min")
                    ),
                    salary_max=self._to_int(
                        item.get("salary_max")
                    ),
                    application_url=item.get(
                        "redirect_url",
                        "",
                    ),
                    source="adzuna",
                    posted_at=posted_at,
                    remote_eligibility=(
                        self._extract_remote_eligibility(
                            item
                        )
                    ),
                )
            )

        return discovered_jobs

    @staticmethod
    def _to_int(value) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_datetime(
        value: str | None,
    ) -> datetime | None:
        if not value:
            return None

        try:
            return datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )
        except ValueError:
            return None

    @staticmethod
    def _extract_work_type(
        item: dict,
    ) -> str | None:
        description = (
            item.get("description") or ""
        ).lower()

        if "part time" in description:
            return "part-time"

        if "contract" in description:
            return "contract"

        if "temporary" in description:
            return "temporary"

        if "full time" in description:
            return "full-time"

        return None

    @staticmethod
    def _extract_remote_eligibility(
        item: dict,
    ) -> str | None:
        description = (
            item.get("description") or ""
        ).lower()

        if "remote" in description:
            return "Remote"

        return None