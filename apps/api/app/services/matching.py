from app.models.career_profile import CareerProfile
from app.models.job import Job


def calculate_match_score(
    profile: CareerProfile,
    job: Job,
) -> tuple[int, list[str]]:
    """
    Calculate a 0-100 match score between a career profile and a job.

    Scoring:
    - Title match:       30 points
    - Experience:        20 points
    - Work type:         20 points
    - Location:          10 points
    - Salary:            20 points
    """

    score = 0
    reasons: list[str] = []

    # --------------------------------------------------
    # 1. TITLE MATCH — 30 POINTS
    # --------------------------------------------------

    if profile.professional_title and job.title:
        profile_title = profile.professional_title.lower()
        job_title = job.title.lower()

        if profile_title in job_title or job_title in profile_title:
            score += 30
            reasons.append("Strong job title match")
        elif any(
            word in job_title
            for word in profile_title.split()
            if len(word) > 2
        ):
            score += 15
            reasons.append("Partial job title match")

    # --------------------------------------------------
    # 2. EXPERIENCE — 20 POINTS
    # --------------------------------------------------

    if profile.years_of_experience is not None:
        # Our current Job model does not have a required
        # experience field, so we give full points for now.
        score += 20
        reasons.append("Experience requirement is currently satisfied")

    # --------------------------------------------------
    # 3. WORK TYPE — 20 POINTS
    # --------------------------------------------------

    if profile.preferred_work_type and job.work_type:
        preferred = profile.preferred_work_type.lower()
        job_type = job.work_type.lower()

        if preferred == job_type:
            score += 20
            reasons.append("Preferred work type matched")
        elif preferred in job_type or job_type in preferred:
            score += 10
            reasons.append("Work type partially matched")
    elif not profile.preferred_work_type:
        score += 20
        reasons.append("No work type preference specified")

    # --------------------------------------------------
    # 4. LOCATION — 10 POINTS
    # --------------------------------------------------

    if profile.preferred_location and job.location:
        preferred_location = profile.preferred_location.lower()
        job_location = job.location.lower()

        if (
            preferred_location in job_location
            or job_location in preferred_location
        ):
            score += 10
            reasons.append("Preferred location matched")
    elif not profile.preferred_location:
        score += 10
        reasons.append("No location preference specified")

    # --------------------------------------------------
    # 5. SALARY — 20 POINTS
    # --------------------------------------------------

    if profile.minimum_salary is not None:
        if job.salary_max is not None:
            if job.salary_max >= profile.minimum_salary:
                score += 20
                reasons.append("Job salary meets minimum requirement")
            elif job.salary_max >= profile.minimum_salary * 0.8:
                score += 10
                reasons.append("Job salary is close to minimum requirement")
    else:
        score += 20
        reasons.append("No minimum salary specified")

    return min(score, 100), reasons