import os

from app.job_sources.adzuna import AdzunaJobSource
from app.job_sources.arbeitnow import ArbeitnowJobSource
from app.job_sources.base import JobSource
from app.job_sources.company_boards import (
    AshbyJobSource,
    GreenhouseJobSource,
    LeverJobSource,
)
from app.job_sources.himalayas import HimalayasJobSource
from app.job_sources.jobicy import JobicyJobSource
from app.job_sources.mock import MockJobSource
from app.job_sources.remoteok import RemoteOKJobSource
from app.job_sources.remotive import RemotiveJobSource
from app.job_sources.weworkremotely import WeWorkRemotelyJobSource


JOB_SOURCE_REGISTRY: dict[str, type[JobSource]] = {
    "adzuna": AdzunaJobSource,
    "arbeitnow": ArbeitnowJobSource,
    "ashby": AshbyJobSource,
    "greenhouse": GreenhouseJobSource,
    "himalayas": HimalayasJobSource,
    "jobicy": JobicyJobSource,
    "lever": LeverJobSource,
    "mock": MockJobSource,
    "remoteok": RemoteOKJobSource,
    "remotive": RemotiveJobSource,
    "weworkremotely": WeWorkRemotelyJobSource,
}


def get_job_sources() -> list[JobSource]:
    """
    Return the configured job sources for JobForge.

    Sources are selected using the JOB_SOURCES environment variable.

    Example:
        JOB_SOURCES=adzuna
        JOB_SOURCES=mock
        JOB_SOURCES=adzuna,mock
        JOB_SOURCES=remotive,remoteok,himalayas,jobicy,arbeitnow,weworkremotely

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