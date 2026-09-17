from app.job_sources.base import JobSource
from app.job_sources.mock import MockJobSource


JOB_SOURCE_REGISTRY: dict[str, type[JobSource]] = {
    "mock": MockJobSource,
}


def get_job_sources() -> list[JobSource]:
    """
    Return the configured job sources for JobForge.

    The registry keeps source selection separate from the monitoring
    and matching logic so new providers can be added later without
    changing the monitoring service.
    """
    return [source_class() for source_class in JOB_SOURCE_REGISTRY.values()]