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


def test_salary_below_minimum_does_not_lower_the_score():
    profile = make_profile(
        minimum_salary=4000,
    )

    low_pay, reasons = calculate_match_score(
        profile,
        make_job(salary_min=2000, salary_max=3000),
    )
    good_pay, _ = calculate_match_score(
        profile,
        make_job(salary_min=4000, salary_max=5000),
    )

    assert low_pay == good_pay
    assert low_pay > 90
    assert "Job salary is below candidate minimum" in reasons
    assert "Job has an eligibility mismatch" not in reasons


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

# ============================================================
# UNSTATED INFORMATION
# ============================================================

def test_missing_experience_and_salary_do_not_lower_the_score():
    profile = make_profile()

    stated, _ = calculate_match_score(profile, make_job())
    unstated, reasons = calculate_match_score(
        profile,
        make_job(
            required_experience=None,
            salary_min=None,
            salary_max=None,
        ),
    )

    assert unstated == stated
    assert unstated > 90
    assert "No specific experience requirement" in reasons
    assert "Job salary is not specified" in reasons


def test_stated_mismatch_still_lowers_the_score():
    profile = make_profile(years_of_experience=1)

    score, _ = calculate_match_score(
        profile,
        make_job(required_experience=6),
    )

    assert score <= 90


def test_job_without_recognisable_skills_is_capped_at_89():
    score, _ = calculate_match_score(
        make_profile(),
        make_job(required_skills="[]"),
    )

    assert score == 89


def test_remote_job_without_stated_countries_is_capped_at_89():
    score, _ = calculate_match_score(
        make_profile(),
        make_job(
            location="Remote",
            remote_eligibility=None,
        ),
    )

    assert score == 89


def test_profile_without_skills_loses_skill_points():
    score, reasons = calculate_match_score(
        make_profile(skills=None),
        make_job(),
    )

    assert score <= 90
    assert "Candidate skills are missing" in reasons


# ============================================================
# SALARY CURRENCY AND PERIOD
# ============================================================

def make_real_job(**overrides):
    # Real sources report yearly salaries with a currency.
    data = {
        "salary_min": 50000,
        "salary_max": 60000,
        "salary_currency": "USD",
        "salary_period": "year",
    }
    data.update(overrides)
    return make_job(**data)


def test_monthly_preference_is_compared_with_yearly_salary():
    # $3,000-$5,000 a month is $36,000-$60,000 a year.
    profile = make_profile(
        minimum_salary=3000,
        maximum_salary=5000,
        salary_currency="USD",
        salary_period="month",
    )

    _, reasons = calculate_match_score(profile, make_real_job())

    assert "Job salary fits candidate salary preference" in reasons


def test_salary_below_monthly_minimum_is_shown_but_not_scored():
    profile = make_profile(
        minimum_salary=5000,
        maximum_salary=8000,
        salary_currency="USD",
        salary_period="month",
    )

    score, reasons = calculate_match_score(
        profile,
        make_real_job(salary_min=30000, salary_max=40000),
    )

    assert score > 90
    assert "Job salary is below candidate minimum" in reasons


def test_yearly_preference_is_compared_directly():
    profile = make_profile(
        minimum_salary=70000,
        maximum_salary=90000,
        salary_currency="USD",
        salary_period="year",
    )

    score, reasons = calculate_match_score(profile, make_real_job())

    assert score > 90
    assert "Job salary is below candidate minimum" in reasons


def test_different_currencies_are_not_compared():
    profile = make_profile(
        minimum_salary=1000000,
        salary_currency="NGN",
        salary_period="month",
    )

    score, reasons = calculate_match_score(profile, make_real_job())

    assert "Job salary is in USD, your preference is in NGN" in reasons
    assert score > 90


def test_salary_not_compared_without_profile_currency():
    _, reasons = calculate_match_score(
        make_profile(salary_currency=None),
        make_real_job(),
    )

    assert (
        "Job salary could not be compared with your preference"
        in reasons
    )



# ============================================================
# UNPAID / VOLUNTEER ROLES
# ============================================================

def test_volunteer_role_is_ineligible():
    score, reasons = calculate_match_score(
        make_profile(),
        make_job(title="Volunteer Frontend Developer"),
    )

    assert score <= 49
    assert "Unpaid or volunteer role" in reasons


def test_unpaid_role_in_description_is_ineligible():
    score, reasons = calculate_match_score(
        make_profile(),
        make_job(description="This is an unpaid internship for students."),
    )

    assert score <= 49
    assert "Unpaid or volunteer role" in reasons


def test_unpaid_leave_benefit_does_not_count_as_unpaid_role():
    score, reasons = calculate_match_score(
        make_profile(),
        make_job(
            description=(
                "Benefits include unpaid leave, volunteering days "
                "and a learning budget."
            ),
        ),
    )

    assert score > 90
    assert "Unpaid or volunteer role" not in reasons


def test_onsite_preference_matches_on_site_jobs():
    _, reasons = calculate_match_score(
        make_profile(preferred_work_type="onsite"),
        make_job(work_type="on-site", location="Lagos, Nigeria"),
    )

    assert "Preferred work type matched" in reasons
