from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.services.matching import calculate_match_score


profile = CareerProfile(
    professional_title="Frontend Developer",
    years_of_experience=3,
    preferred_work_type="Remote",
    preferred_location="Lagos",
    minimum_salary=2500,
)

job = Job(
    title="Frontend Developer",
    company="Test Company",
    work_type="Remote",
    location="Lagos",
    salary_min=3000,
    salary_max=4000,
    application_url="https://example.com",
    source="test",
    fingerprint="test-fingerprint-123",
)

score, reasons = calculate_match_score(profile, job)

print("Score:", score)
print("Reasons:")

for reason in reasons:
    print("-", reason)