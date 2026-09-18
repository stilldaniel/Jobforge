import os

from app.job_sources.adzuna import AdzunaJobSource
from app.job_sources.base import JobSource
from app.job_sources.mock import MockJobSource


JOB_SOURCE_REGISTRY: dict[str, type[JobSource]] = {
    "adzuna": AdzunaJobSource,
    "mock": MockJobSource,
}


def get_job_sources() -> list[JobSource]:
    """
    Return the configured job sources for JobForge.

    Sources are selected using the JOB_SOURCES environment variable.

    Example:
        JOB_SOURCES=adzuna
        JOB_SOURCES=mock
        JOB_SOURCES=adzuna,mock

    If JOB_SOURCES is not configured, MockJobSource is used as the
    safe development default.
    """
    configured_sources = os.getenv("JOB_SOURCES", "mock")

    source_names = [
        name.strip().lower()
        for name in configured_sources.split(",")
        if name.strip()
    ]

    if not source_names:
        source_names = ["mock"]

    sources: list[JobSource] = []

    for source_name in source_names:
        source_class = JOB_SOURCE_REGISTRY.get(source_name)

        if source_class is None:
            raise ValueError(
                f"Unknown job source: {source_name}"
            )

        sources.append(source_class())

    return sources