from datetime import datetime, timezone

from app.job_sources.base import DiscoveredJob, JobSource


class MockJobSource(JobSource):

    def fetch_jobs(self) -> list[DiscoveredJob]:
        return [
            DiscoveredJob(
                title="Senior Frontend Developer",
                company="TechFlow",
                description=(
                    "We are looking for a senior frontend developer "
                    "with 4+ years of experience building modern web "
                    "applications. Strong experience with React, "
                    "TypeScript, Next.js, JavaScript, Git and Tailwind CSS "
                    "is required."
                ),
                location="Remote",
                work_type="remote",
                salary_min=3000,
                salary_max=5000,
                application_url=(
                    "https://example.com/jobs/senior-frontend-developer"
                ),
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),
            DiscoveredJob(
                title="React Developer",
                company="CloudWorks",
                description=(
                    "Build modern web applications using React, "
                    "TypeScript and modern frontend technologies. "
                    "Requires 1+ year of experience with React and "
                    "JavaScript. Experience with Git and HTML is preferred."
                ),
                location="Remote",
                work_type="remote",
                salary_min=2500,
                salary_max=4500,
                application_url=(
                    "https://example.com/jobs/react-developer"
                ),
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),
            DiscoveredJob(
                title="Frontend Developer",
                company="Example Technologies",
                description=(
                    "We are looking for a frontend developer with "
                    "2+ years of experience. Experience with React, "
                    "TypeScript, JavaScript, HTML, CSS and Git is required."
                ),
                location="Worldwide",
                work_type="remote",
                salary_min=2000,
                salary_max=3500,
                application_url=(
                    "https://example.com/jobs/frontend-developer"
                ),
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),
        ]