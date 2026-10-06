"""
Turn users' career profiles into what job sources need: search
queries for platforms with a search API, and keywords for discarding
irrelevant jobs from platforms that only offer a full feed.
"""

from dataclasses import dataclass, field

from app.job_sources.base import DiscoveredJob
from app.models.career_profile import CareerProfile
from app.services.matching import (
    ALIASES,
    _normalize_skills,
    _normalize_text,
    _tokenize,
)


# Title words that say nothing about the field of work.
GENERIC_TITLE_WORDS = {
    "a",
    "and",
    "associate",
    "developer",
    "engineer",
    "head",
    "i",
    "ii",
    "iii",
    "intern",
    "junior",
    "jr",
    "lead",
    "level",
    "mid",
    "of",
    "principal",
    "senior",
    "software",
    "sr",
    "staff",
    "the",
}


def _title_terms(value: str | None) -> set[str]:
    """
    Words in a title, plus adjacent word pairs joined together so that
    "Front-End" and "Full Stack" compare equal to "frontend" and
    "fullstack".
    """

    tokens = _tokenize(value)
    words = _normalize_text(value).split()

    for first, second in zip(words, words[1:]):
        pair = f"{first} {second}"
        tokens.add(ALIASES.get(pair, first + second))

    return tokens


@dataclass
class SearchCriteria:
    queries: list[str] = field(default_factory=list)
    title_keywords: set[str] = field(default_factory=set)
    skill_keywords: set[str] = field(default_factory=set)

    @property
    def is_empty(self) -> bool:
        return not (
            self.queries
            or self.title_keywords
            or self.skill_keywords
        )


def build_search_criteria(
    profiles: list[CareerProfile],
) -> SearchCriteria:
    criteria = SearchCriteria()

    for profile in profiles:
        title = _normalize_text(profile.professional_title)

        if title and title not in criteria.queries:
            criteria.queries.append(title)

        title_tokens = _title_terms(profile.professional_title)
        specific_tokens = title_tokens - GENERIC_TITLE_WORDS

        # A title made only of generic words ("Software Engineer")
        # is still the best signal available for that profile.
        criteria.title_keywords.update(
            specific_tokens or title_tokens
        )

        criteria.skill_keywords.update(
            _normalize_skills(profile.skills)
        )

    return criteria


def is_relevant(
    job: DiscoveredJob,
    criteria: SearchCriteria,
) -> bool:
    """
    A job is relevant when its title mentions a specific word from a
    profile's title (e.g. "frontend") or one of a profile's skills
    (e.g. "react"). Only the title is checked: descriptions mention
    many technologies the role isn't about.
    """

    title = _normalize_text(job.title)
    title_tokens = _title_terms(job.title)

    if title_tokens & criteria.title_keywords:
        return True

    for skill in criteria.skill_keywords:
        if " " in skill:
            if f" {skill} " in f" {title} ":
                return True
        elif skill in title_tokens:
            return True

    return False


def has_field_fit(
    profile: CareerProfile,
    job,
) -> bool:
    """
    Whether a job is in the candidate's field at all: its title shares
    a specific word with the profile title or names one of their
    skills, or it requires at least one of their skills.

    Generic title words ("developer", "senior") don't count, so a
    Backend Developer job is not a fit for a Frontend Developer unless
    the skills overlap.
    """

    criteria = build_search_criteria([profile])

    if is_relevant(job, criteria):
        return True

    required_skills = _normalize_skills(
        getattr(job, "required_skills", None)
    )

    return bool(required_skills & criteria.skill_keywords)
