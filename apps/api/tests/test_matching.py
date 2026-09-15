from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.services.matching import calculate_match_score


def make_profile(**overrides):
    data = {
        "professional_title": "Frontend Developer",
        "skills": "React, Next.js, TypeScript, JavaScript",
        "years_of_experience": 5,
        "candidate_location": "Lagos, Nigeria",
        "preferred_work_type": "remote",
        "preferred_location": "Worldwide",
        "minimum_salary": 2500,
        "maximum_salary": 5000,
    }

    data.update(overrides)

    return CareerProfile(**data)


def make_job(**overrides):
    data = {
        "title": "Frontend Developer",
        "company": "Test Company",
        "description": "Build modern web applications.",
        "required_skills": "React, Next.js, TypeScript",
        "required_experience": 3,
        "location": "Lagos, Nigeria",
        "remote_eligibility": "Worldwide",
        "work_type": "remote",
        "salary_min": 3000,
        "salary_max": 4000,
        "application_url": "https://example.com",
        "source": "test",
        "fingerprint": "test-fingerprint",
    }

    data.update(overrides)

    return Job(**data)


def test_strong_match_scores_above_90():
    profile = make_profile()

    job = make_job(
        remote_eligibility="Worldwide",
    )

    score, reasons = calculate_match_score(
        profile,
        job,
    )

    assert score > 90
    assert reasons


def test_salary_below_minimum_makes_job_ineligible():
    profile = make_profile(
        minimum_salary=4000,
    )

    job = make_job(
        salary_min=2000,
        salary_max=3000,
    )

    score, reasons = calculate_match_score(
        profile,
        job,
    )

    assert score < 50


def test_location_mismatch_makes_job_ineligible():
    profile = make_profile(
        candidate_location="Lagos, Nigeria",
        preferred_location="Lagos, Nigeria",
    )

    job = make_job(
        location="London, United Kingdom",
        remote_eligibility="",
        work_type="onsite",
    )

    score, reasons = calculate_match_score(
        profile,
        job,
    )

    assert score < 50


def test_remote_worldwide_job_can_match_candidate():
    profile = make_profile(
        candidate_location="Lagos, Nigeria",
        preferred_location="Worldwide",
        preferred_work_type="remote",
    )

    job = make_job(
        location="New York, United States",
        remote_eligibility="Worldwide",
        work_type="remote",
    )

    score, reasons = calculate_match_score(
        profile,
        job,
    )

    assert score > 90
    assert reasons


def test_remote_job_with_unknown_geographic_scope_is_capped():
    profile = make_profile(
        candidate_location="Lagos, Nigeria",
        preferred_location="Worldwide",
        preferred_work_type="remote",
    )

    job = make_job(
        location="New York, United States",
        remote_eligibility="remote",
        work_type="remote",
    )

    score, reasons = calculate_match_score(
        profile,
        job,
    )

    assert score > 49
    assert score <= 89
    assert reasons


def test_explicit_remote_country_match_is_eligible():
    profile = make_profile(
        candidate_location="Lagos, Nigeria",
        preferred_location="Worldwide",
        preferred_work_type="remote",
    )

    job = make_job(
        location="New York, United States",
        remote_eligibility="Nigeria",
        work_type="remote",
    )

    score, reasons = calculate_match_score(
        profile,
        job,
    )

    assert score > 90
    assert reasons


def test_explicit_remote_country_mismatch_makes_job_ineligible():
    profile = make_profile(
        candidate_location="Lagos, Nigeria",
        preferred_location="Worldwide",
        preferred_work_type="remote",
    )

    job = make_job(
        location="New York, United States",
        remote_eligibility="United States",
        work_type="remote",
    )

    score, reasons = calculate_match_score(
        profile,
        job,
    )

    assert score < 50
    assert reasons


def test_work_type_mismatch_does_not_make_job_ineligible():
    profile = make_profile(
        preferred_work_type="remote",
    )

    job = make_job(
        work_type="hybrid",
        remote_eligibility="hybrid",
        location="Lagos, Nigeria",
    )

    score, reasons = calculate_match_score(
        profile,
        job,
    )

    assert score >= 50
    assert reasons


def test_unknown_remote_eligibility_cannot_score_above_89():
    profile = make_profile(
        preferred_location="Worldwide",
        preferred_work_type="remote",
    )

    job = make_job(
        location="Lagos, Nigeria",
        remote_eligibility="remote",
        work_type="remote",
    )

    score, reasons = calculate_match_score(
        profile,
        job,
    )

    assert score <= 89
    assert score > 49
    assert reasons


def test_experience_shortfall_does_not_make_job_ineligible():
    profile = make_profile(
        years_of_experience=2,
    )

    job = make_job(
        required_experience=5,
        remote_eligibility="Worldwide",
    )

    score, reasons = calculate_match_score(
        profile,
        job,
    )

    assert score >= 50
    assert reasons