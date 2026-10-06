import hashlib
import re


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

COMPANY_SUFFIXES = {
    "inc",
    "incorporated",
    "llc",
    "ltd",
    "limited",
    "plc",
    "gmbh",
    "ag",
    "sa",
    "bv",
    "co",
    "corp",
    "corporation",
    "company",
    "group",
    "technologies",
    "technology",
}

# Words platforms add to titles that don't change the role itself.
TITLE_NOISE = {
    "remote",
    "hybrid",
    "onsite",
    "worldwide",
    "anywhere",
    "fulltime",
    "parttime",
    "contract",
    "m",
    "f",
    "d",
    "w",
    "x",
}


def _words(value: str) -> list[str]:
    value = value.lower()
    value = re.sub(r"\(.*?\)|\[.*?\]", " ", value)
    value = value.replace("full-time", "fulltime")
    value = value.replace("part-time", "parttime")
    value = value.replace("on-site", "onsite")

    return re.findall(r"[a-z0-9+#.]+", value)


def normalize_company(company: str) -> str:
    words = [
        word.strip(".")
        for word in _words(company)
    ]

    while len(words) > 1 and words[-1] in COMPANY_SUFFIXES:
        words.pop()

    return " ".join(word for word in words if word)


def normalize_title(title: str) -> str:
    return " ".join(
        word.strip(".")
        for word in _words(title)
        if word.strip(".") and word.strip(".") not in TITLE_NOISE
    )


def generate_dedupe_key(
    title: str,
    company: str,
) -> str:
    """
    Key for recognising one job posted on several platforms.

    Unlike the fingerprint it ignores the URL, which differs per
    platform, and normalises small differences such as "Inc." or
    "(Remote)".
    """

    value = "|".join(
        [
            normalize_title(title),
            normalize_company(company),
        ]
    )

    return hashlib.sha256(value.encode("utf-8")).hexdigest()
