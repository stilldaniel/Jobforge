import json
import re

from app.models.career_profile import CareerProfile
from app.models.job import Job


def normalize_text(value: str | None) -> str:
    """
    Normalize text for reliable comparisons.
    """
    if not value:
        return ""

    return re.sub(r"\s+", " ", value.strip().lower())


def parse_skills(value: str | None) -> list[str]:
    """
    Convert a JSON skills string into a normalized list of skills.
    """

    if not value:
        return []

    try:
        skills = json.loads(value)

        if isinstance(skills, list):
            return [
                normalize_text(skill)
                for skill in skills
                if isinstance(skill, str)
            ]

    except (json.JSONDecodeError, TypeError):
        pass

    return []


def calculate_match_score(
    profile: CareerProfile,
    job: Job,
) -> tuple[int, list[str]]:
    """
    Calculate a 0-100 match score between a career profile and a job.

    Scoring:
    - Title:       25 points
    - Skills:      30 points
    - Experience:  20 points
    - Work type:   10 points
    - Location:     5 points
    - Salary:      10 points
    """

    score = 0
    reasons: list[str] = []

    # --------------------------------------------------
    # 1. TITLE MATCH — 25 POINTS
    # --------------------------------------------------

    profile_title = normalize_text(profile.professional_title)
    job_title = normalize_text(job.title)

    if profile_title and job_title:

        if profile_title in job_title or job_title in profile_title:
            score += 25
            reasons.append("Strong job title match")

        else:
            profile_words = {
                word
                for word in profile_title.split()
                if len(word) > 2
            }

            job_words = set(job_title.split())

            matching_words = profile_words.intersection(job_words)

            if matching_words:
                score += 12
                reasons.append("Partial job title match")

    # --------------------------------------------------
    # 2. SKILLS MATCH — 30 POINTS
    # --------------------------------------------------

    candidate_skills = parse_skills(profile.skills)
    required_skills = parse_skills(job.required_skills)

    if required_skills:

        if candidate_skills:

            matched_skills = [
                skill
                for skill in required_skills
                if skill in candidate_skills
            ]

            skill_count = len(required_skills)
            matched_count = len(matched_skills)

            skill_ratio = matched_count / skill_count
            skill_points = round(skill_ratio * 30)

            score += skill_points

            if matched_count == skill_count:
                reasons.append("All required skills matched")

            elif matched_count > 0:
                reasons.append(
                    f"{matched_count} of {skill_count} required skills matched"
                )

            else:
                reasons.append("No required skills matched")

        else:
            reasons.append("No candidate skills provided")

    else:
        score += 30
        reasons.append("No specific skills requirement provided")

    # --------------------------------------------------
    # 3. EXPERIENCE — 20 POINTS
    # --------------------------------------------------

    user_experience = profile.years_of_experience or 0
    required_experience = job.required_experience

    if required_experience is None:
        score += 20
        reasons.append("No specific experience requirement provided")

    elif user_experience >= required_experience:
        score += 20
        reasons.append("Experience requirement satisfied")

    elif user_experience >= required_experience * 0.75:
        score += 10
        reasons.append("Experience is close to requirement")

    else:
        reasons.append("Experience requirement not satisfied")

    # --------------------------------------------------
    # 4. WORK TYPE — 10 POINTS
    # --------------------------------------------------

    preferred_work_type = normalize_text(
        profile.preferred_work_type
    )

    job_work_type = normalize_text(job.work_type)

    if not preferred_work_type:
        score += 10
        reasons.append("No work type preference specified")

    elif not job_work_type:
        score += 5
        reasons.append("Job does not specify a work type")

    elif preferred_work_type == job_work_type:
        score += 10
        reasons.append("Preferred work type matched")

    elif (
        preferred_work_type in job_work_type
        or job_work_type in preferred_work_type
    ):
        score += 5
        reasons.append("Work type partially matched")

    # --------------------------------------------------
    # 5. LOCATION — 5 POINTS
    # --------------------------------------------------

    preferred_location = normalize_text(
        profile.preferred_location
    )

    job_location = normalize_text(job.location)

    if not preferred_location:
        score += 5
        reasons.append("No location preference specified")

    elif not job_location:
        score += 2
        reasons.append("Job does not specify a location")

    elif (
        preferred_location in job_location
        or job_location in preferred_location
    ):
        score += 5
        reasons.append("Preferred location matched")

    # --------------------------------------------------
    # 6. SALARY — 10 POINTS
    # --------------------------------------------------

    minimum_salary = profile.minimum_salary

    if minimum_salary is None:
        score += 10
        reasons.append("No minimum salary specified")

    elif job.salary_max is None:
        score += 5
        reasons.append("Job does not specify a salary")

    elif job.salary_max >= minimum_salary:
        score += 10
        reasons.append("Job salary meets minimum requirement")

    elif job.salary_max >= minimum_salary * 0.8:
        score += 5
        reasons.append("Job salary is close to minimum requirement")

    # --------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------

    return min(score, 100), reasons