import hashlib


def generate_job_fingerprint(
    title: str,
    company: str,
    application_url: str,
) -> str:
    value = "|".join(
        [
            title.strip().lower(),
            company.strip().lower(),
            application_url.strip().lower(),
        ]
    )

    return hashlib.sha256(value.encode("utf-8")).hexdigest()