from __future__ import annotations

import json
import re
from typing import Any


# ============================================================
# SCORING WEIGHTS
# ============================================================

TITLE_WEIGHT = 25
SKILLS_WEIGHT = 30
EXPERIENCE_WEIGHT = 15
WORK_TYPE_WEIGHT = 10
LOCATION_WEIGHT = 10
SALARY_WEIGHT = 10


# ============================================================
# NORMALIZATION / ALIASES
# ============================================================

ALIASES = {
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",
    "react": "react",
    "nextjs": "next.js",
    "next.js": "next.js",
    "next js": "next.js",
    "frontend": "frontend",
    "front-end": "frontend",
    "front end": "frontend",
    "backend": "backend",
    "back-end": "backend",
    "back end": "backend",
    "tailwind": "tailwind css",
    "tailwindcss": "tailwind css",
    "tailwind css": "tailwind css",
    "html5": "html",
    "css3": "css",
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
}


WORLDWIDE_TERMS = {
    "worldwide",
    "global",
    "anywhere",
    "international",
    "world wide",
}


REMOTE_TERMS = {
    "remote",
    "work from home",
    "wfh",
    "fully remote",
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def _normalize_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip().lower()
    text = text.replace("_", " ")
    text = text.replace("-", " ")
    text = re.sub(r"[^\w\s.]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _normalize_alias(value: Any) -> str:
    normalized = _normalize_text(value)
    return ALIASES.get(normalized, normalized)


def _parse_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    value = str(value).strip()

    if not value:
        return []

    try:
        parsed = json.loads(value)

        if isinstance(parsed, list):
            return [
                str(item).strip()
                for item in parsed
                if str(item).strip()
            ]

    except (json.JSONDecodeError, TypeError):
        pass

    parts = re.split(r"[,;|\n]+", value)

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def _normalize_skills(value: Any) -> set[str]:
    skills = _parse_list(value)

    normalized = set()

    for skill in skills:
        skill = _normalize_alias(skill)

        if skill:
            normalized.add(skill)

    return normalized


def _tokenize(value: Any) -> set[str]:
    text = _normalize_text(value)

    if not text:
        return set()

    tokens = text.split()

    return {
        _normalize_alias(token)
        for token in tokens
        if token
    }


def _location_tokens(value: Any) -> set[str]:
    text = _normalize_text(value)

    if not text:
        return set()

    tokens = set(text.split())

    if "usa" in tokens or "us" in tokens:
        tokens.update(
            {
                "usa",
                "us",
                "united",
                "states",
            }
        )

    if "united" in tokens and "states" in tokens:
        tokens.update(
            {
                "usa",
                "us",
            }
        )

    if "uk" in tokens:
        tokens.update(
            {
                "uk",
                "united",
                "kingdom",
            }
        )

    if "united" in tokens and "kingdom" in tokens:
        tokens.add("uk")

    if "uae" in tokens:
        tokens.update(
            {
                "uae",
                "united",
                "arab",
                "emirates",
            }
        )

    if "nigeria" in tokens:
        tokens.add("ng")

    return tokens


def _contains_worldwide(value: Any) -> bool:
    text = _normalize_text(value)

    return any(
        term in text
        for term in WORLDWIDE_TERMS
    )


def _is_remote_job(job: Any) -> bool:
    work_type = _normalize_text(
        getattr(job, "work_type", None)
    )

    location = _normalize_text(
        getattr(job, "location", None)
    )

    remote_eligibility = _normalize_text(
        getattr(job, "remote_eligibility", None)
    )

    return (
        work_type in REMOTE_TERMS
        or "remote" in work_type
        or "remote" in location
        or "remote" in remote_eligibility
    )


# ============================================================
# TITLE MATCHING
# ============================================================

def _title_score(
    profile: Any,
    job: Any,
) -> tuple[int | None, str]:

    candidate_title = _normalize_text(
        getattr(
            profile,
            "professional_title",
            None,
        )
    )

    job_title = _normalize_text(
        getattr(
            job,
            "title",
            None,
        )
    )

    if not candidate_title or not job_title:
        return (
            0,
            "Title information is missing",
        )

    if candidate_title == job_title:
        return (
            TITLE_WEIGHT,
            "Exact job title match",
        )

    candidate_tokens = _tokenize(
        candidate_title
    )

    job_tokens = _tokenize(
        job_title
    )

    if not candidate_tokens or not job_tokens:
        return (
            0,
            "Job title could not be compared",
        )

    common = candidate_tokens.intersection(
        job_tokens
    )

    overlap = len(common) / max(
        len(candidate_tokens),
        len(job_tokens),
    )

    if (
        "frontend" in candidate_tokens
        and "frontend" in job_tokens
    ):
        if overlap >= 0.5:
            return (
                22,
                "Strong frontend job title match",
            )

        return (
            20,
            "Related frontend job title",
        )

    if overlap >= 0.75:
        return (
            20,
            "Strong job title match",
        )

    if overlap >= 0.5:
        return (
            16,
            "Related job title",
        )

    if common:
        return (
            10,
            "Some job title similarity",
        )

    return (
        0,
        "Job title is not closely related",
    )


# ============================================================
# SKILL MATCHING
# ============================================================

def _skills_score(
    profile: Any,
    job: Any,
) -> tuple[int | None, str]:

    candidate_skills = _normalize_skills(
        getattr(
            profile,
            "skills",
            None,
        )
    )

    required_skills = _normalize_skills(
        getattr(
            job,
            "required_skills",
            None,
        )
    )

    # No recognisable skills in the job text is not evidence of a fit,
    # so it earns no points; otherwise unrelated jobs (sales, support)
    # would score close to genuine matches.
    if not required_skills:
        return (
            None,
            "No specific required skills listed",
        )

    if not candidate_skills:
        return (
            0,
            "Candidate skills are missing",
        )

    matched = candidate_skills.intersection(
        required_skills
    )

    match_ratio = (
        len(matched) / len(required_skills)
    )

    score = round(
        match_ratio * SKILLS_WEIGHT
    )

    if match_ratio == 1:
        reason = "All required skills matched"

    elif match_ratio >= 0.75:
        reason = (
            f"Most required skills matched "
            f"({len(matched)}/{len(required_skills)})"
        )

    elif match_ratio >= 0.5:
        reason = (
            f"Some required skills matched "
            f"({len(matched)}/{len(required_skills)})"
        )

    elif matched:
        reason = (
            f"Few required skills matched "
            f"({len(matched)}/{len(required_skills)})"
        )

    else:
        reason = (
            "Required skills did not match"
        )

    return score, reason


# ============================================================
# EXPERIENCE MATCHING
# ============================================================

def _experience_score(
    profile: Any,
    job: Any,
) -> tuple[int | None, str, bool]:

    candidate_experience = getattr(
        profile,
        "years_of_experience",
        0,
    ) or 0

    required_experience = getattr(
        job,
        "required_experience",
        None,
    )

    if required_experience is None:
        return (
            None,
            "No specific experience requirement",
            False,
        )

    try:
        candidate_experience = int(
            candidate_experience
        )

        required_experience = int(
            required_experience
        )

    except (TypeError, ValueError):
        return (
            None,
            "Experience requirement could not be evaluated",
            False,
        )

    if candidate_experience >= required_experience:
        return (
            EXPERIENCE_WEIGHT,
            "Experience requirement satisfied",
            False,
        )

    difference = (
        required_experience
        - candidate_experience
    )

    if difference == 1:
        return (
            10,
            "Candidate is one year below the experience requirement",
            False,
        )

    if difference == 2:
        return (
            6,
            "Candidate is two years below the experience requirement",
            False,
        )

    if difference == 3:
        return (
            3,
            "Candidate is three years below the experience requirement",
            False,
        )

    return (
        0,
        "Candidate is significantly below the experience requirement",
        False,
    )


# ============================================================
# WORK TYPE
# ============================================================

def _work_type_score(
    profile: Any,
    job: Any,
) -> tuple[int | None, str, bool]:

    preferred = _normalize_text(
        getattr(
            profile,
            "preferred_work_type",
            None,
        )
    )

    actual = _normalize_text(
        getattr(
            job,
            "work_type",
            None,
        )
    )

    if not preferred:
        return (
            None,
            "No preferred work type specified",
            False,
        )

    if not actual:
        return (
            None,
            "Job work type is not specified",
            False,
        )

    preferred = preferred.replace(
        "-",
        " ",
    )

    actual = actual.replace(
        "-",
        " ",
    )

    if preferred == actual:
        return (
            WORK_TYPE_WEIGHT,
            "Preferred work type matched",
            False,
        )

    if (
        preferred == "remote"
        and "remote" in actual
    ):
        return (
            WORK_TYPE_WEIGHT,
            "Preferred remote work type matched",
            False,
        )

    # Work type mismatch is a negative preference,
    # but it is NOT a hard eligibility failure.
    return (
        0,
        "Preferred work type does not match",
        False,
    )


# ============================================================
# LOCATION / REMOTE ELIGIBILITY
# ============================================================

def _location_score(
    profile: Any,
    job: Any,
) -> tuple[int | None, str, bool]:

    candidate_location = _normalize_text(
        getattr(
            profile,
            "candidate_location",
            None,
        )
    )

    preferred_location = _normalize_text(
        getattr(
            profile,
            "preferred_location",
            None,
        )
    )

    job_location = _normalize_text(
        getattr(
            job,
            "location",
            None,
        )
    )

    remote_eligibility = _normalize_text(
        getattr(
            job,
            "remote_eligibility",
            None,
        )
    )

    candidate_tokens = _location_tokens(
        candidate_location
    )

    job_location_tokens = _location_tokens(
        job_location
    )

    eligibility_tokens = _location_tokens(
        remote_eligibility
    )

    # ========================================================
    # REMOTE JOB
    # ========================================================

    if _is_remote_job(job):

        # Explicitly worldwide / unrestricted remote.
        if (
            _contains_worldwide(
                remote_eligibility
            )
            or _contains_worldwide(
                job_location
            )
        ):
            return (
                LOCATION_WEIGHT,
                "Remote job accepts candidates worldwide",
                False,
            )

        # Explicit geographic eligibility.
        #
        # "Nigeria", "Lagos", "United States", etc.
        # represent geographic restrictions.
        #
        # "remote", "wfh", and similar values only describe
        # the work arrangement and do not specify geography.
        if (
            remote_eligibility
            and remote_eligibility not in REMOTE_TERMS
        ):
            if candidate_tokens.intersection(
                eligibility_tokens
            ):
                return (
                    LOCATION_WEIGHT,
                    "Remote job accepts candidates from candidate location",
                    False,
                )

            return (
                0,
                "Remote job does not accept candidates from candidate location",
                True,
            )

        # Remote, but geographic eligibility is unknown.
        return (
            None,
            "Remote eligibility is not geographically specified",
            False,
        )

    # ========================================================
    # NON-REMOTE JOB
    # ========================================================

    if not job_location:
        return (
            None,
            "Job location is not specified",
            False,
        )

    if candidate_tokens.intersection(
        job_location_tokens
    ):
        return (
            LOCATION_WEIGHT,
            "Job location matches candidate location",
            False,
        )

    preferred_tokens = _location_tokens(
        preferred_location
    )

    if preferred_tokens.intersection(
        job_location_tokens
    ):
        return (
            LOCATION_WEIGHT,
            "Job location matches preferred location",
            False,
        )

    return (
        0,
        "Job location does not match candidate location",
        True,
    )


# ============================================================
# SALARY
# ============================================================

def _salary_score(
    profile: Any,
    job: Any,
) -> tuple[int | None, str, bool]:

    minimum_salary = getattr(
        profile,
        "minimum_salary",
        None,
    )

    maximum_salary = getattr(
        profile,
        "maximum_salary",
        None,
    )

    salary_min = getattr(
        job,
        "salary_min",
        None,
    )

    salary_max = getattr(
        job,
        "salary_max",
        None,
    )

    if (
        minimum_salary is None
        and maximum_salary is None
    ):
        return (
            None,
            "No salary preference specified",
            False,
        )

    if (
        salary_min is None
        and salary_max is None
    ):
        return (
            None,
            "Job salary is not specified",
            False,
        )

    # Real job sources report a currency and period (normalised to
    # yearly). Career profiles don't record either yet, so a yearly USD
    # figure can't be compared with, say, a monthly NGN preference.
    if (
        getattr(job, "salary_currency", None)
        or getattr(job, "salary_period", None)
    ):
        return (
            None,
            "Job salary could not be compared with your preference",
            False,
        )

    try:
        minimum_salary = (
            float(minimum_salary)
            if minimum_salary is not None
            else None
        )

        maximum_salary = (
            float(maximum_salary)
            if maximum_salary is not None
            else None
        )

        salary_min = (
            float(salary_min)
            if salary_min is not None
            else None
        )

        salary_max = (
            float(salary_max)
            if salary_max is not None
            else None
        )

    except (TypeError, ValueError):
        return (
            None,
            "Salary information could not be evaluated",
            False,
        )

    # Job is completely below candidate minimum.
    if (
        minimum_salary is not None
        and salary_max is not None
        and salary_max < minimum_salary
    ):
        return (
            0,
            "Job salary is below candidate minimum",
            True,
        )

    overlaps_preference = True

    if (
        maximum_salary is not None
        and salary_min is not None
    ):
        overlaps_preference = (
            salary_min <= maximum_salary
        )

    if overlaps_preference:
        return (
            SALARY_WEIGHT,
            "Job salary fits candidate salary preference",
            False,
        )

    return (
        8,
        "Job salary meets the minimum requirement",
        False,
    )


# ============================================================
# MAIN MATCHING FUNCTION
# ============================================================

def calculate_match_score(
    profile: Any,
    job: Any,
) -> tuple[int, list[str]]:
    """
    Score how well a job matches a career profile, from 0 to 100.

    Only factors the job actually states are scored, and the result is
    scaled to 100. A job that doesn't mention salary or years of
    experience is judged on what it does say, rather than losing points
    for the missing information. Factors the job states but the
    candidate doesn't match still cost points.
    """

    reasons: list[str] = []
    earned = 0
    possible = 0

    def add(
        points: int | None,
        reason: str,
        weight: int,
    ) -> None:
        nonlocal earned, possible

        reasons.append(reason)

        if points is None:
            return

        earned += points
        possible += weight

    # --------------------------------------------------------
    # FACTORS
    # --------------------------------------------------------

    title_points, title_reason = _title_score(profile, job)
    add(title_points, title_reason, TITLE_WEIGHT)

    skill_points, skill_reason = _skills_score(profile, job)
    add(skill_points, skill_reason, SKILLS_WEIGHT)

    experience_points, experience_reason, _ = _experience_score(
        profile,
        job,
    )
    add(experience_points, experience_reason, EXPERIENCE_WEIGHT)

    work_type_points, work_type_reason, _ = _work_type_score(
        profile,
        job,
    )
    add(work_type_points, work_type_reason, WORK_TYPE_WEIGHT)

    location_points, location_reason, location_problem = _location_score(
        profile,
        job,
    )
    add(location_points, location_reason, LOCATION_WEIGHT)

    salary_points, salary_reason, salary_problem = _salary_score(
        profile,
        job,
    )
    add(salary_points, salary_reason, SALARY_WEIGHT)

    score = round(earned / possible * 100) if possible else 0

    # ========================================================
    # ELIGIBILITY CAPS
    # ========================================================

    # Experience and work type are deliberately NOT hard failures:
    # they reduce the score but don't make the job ineligible.
    #
    # Geographic incompatibility and salary below the candidate's
    # minimum remain hard eligibility failures.

    hard_ineligible = (
        location_problem
        or salary_problem
    )

    if hard_ineligible:
        score = min(
            score,
            49,
        )

        reasons.insert(
            0,
            "Job has an eligibility mismatch",
        )

    # --------------------------------------------------------
    # Less certain matches
    # --------------------------------------------------------
    #
    # Capped at 89 so they never show as a perfect score:
    # - Remote with unknown geography: many "remote" jobs only hire
    #   in one country.
    # - No recognisable skills: the job can't be judged on what the
    #   role actually involves.

    job_is_remote = _is_remote_job(job)

    remote_eligibility = _normalize_text(
        getattr(
            job,
            "remote_eligibility",
            None,
        )
    )

    geographic_scope_unknown = (
        job_is_remote
        and (
            not remote_eligibility
            or remote_eligibility in REMOTE_TERMS
        )
    )

    skills_unknown = skill_points is None

    if (
        (geographic_scope_unknown or skills_unknown)
        and not hard_ineligible
    ):
        score = min(
            score,
            89,
        )

    # --------------------------------------------------------
    # Final bounds
    # --------------------------------------------------------

    score = max(
        0,
        min(
            100,
            score,
        ),
    )

    return score, reasons
